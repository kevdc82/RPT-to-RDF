"""
Pipeline Orchestration for RPT to RDF Converter.

Coordinates the full conversion pipeline from RPT to RDF.
Supports parallel processing for batch conversions.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Callable, Optional

from .config import Config, get_config
from .extraction.rpt_extractor import RptExtractor, DockerRptExtractor, ExtractionResult, MockRptExtractor
from .parsing.crystal_parser import CrystalParser
from .parsing.report_model import ReportModel
from .transformation.transformer import Transformer, TransformedReport
from .generation.oracle_xml_generator import OracleXMLGenerator
from .generation.rdf_converter import RDFConverter, ConversionResult, MockRDFConverter
from .utils.logger import get_logger, ConversionProgressTracker
from .utils.error_handler import (
    ConversionReport,
    PartialConversion,
    FailedConversion,
    ErrorCategory,
    ConversionError,
)
from .utils.file_utils import get_rpt_files, get_output_path, ensure_directory


@dataclass
class PipelineResult:
    """Result of processing a single report through the pipeline."""

    rpt_path: Path
    rdf_path: Optional[Path]
    status: str  # success, partial, failed
    extraction_result: Optional[ExtractionResult] = None
    report_model: Optional[ReportModel] = None
    transformed_report: Optional[TransformedReport] = None
    rdf_result: Optional[ConversionResult] = None
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class Pipeline:
    """Orchestrates the full RPT to RDF conversion pipeline."""

    def __init__(
        self,
        config: Optional[Config] = None,
        use_mock: bool = False,
        skip_rdf: bool = False,
    ):
        """Initialize the pipeline.

        Args:
            config: Configuration object. If None, loads default config.
            use_mock: If True, use mock extractors/converters for testing.
            skip_rdf: If True, skip RDF conversion (output XML instead).
        """
        self.config = config or get_config()
        self.use_mock = use_mock
        self.skip_rdf = skip_rdf
        self.logger = get_logger("pipeline")

        # Initialize components
        if use_mock:
            self.extractor = MockRptExtractor(
                rpttoxml_path=self.config.extraction.rpttoxml_path,
                temp_dir=self.config.extraction.temp_directory,
                timeout_seconds=self.config.extraction.timeout_seconds,
                retry_attempts=self.config.extraction.retry_attempts,
            )
            self.rdf_converter = MockRDFConverter(
                oracle_home=self.config.oracle.home or "/mock/oracle",
                db_connection=self.config.oracle.connection or "mock/mock@mock",
            )
        else:
            # Select extractor based on mode
            extraction_mode = self.config.extraction.mode
            if extraction_mode == "docker":
                self.extractor = DockerRptExtractor(
                    temp_dir=self.config.extraction.temp_directory,
                    timeout_seconds=self.config.extraction.timeout_seconds,
                    retry_attempts=self.config.extraction.retry_attempts,
                    docker_image=self.config.extraction.docker.image,
                )
            else:
                # java or dotnet mode
                self.extractor = RptExtractor(
                    rpttoxml_path=self.config.extraction.rpttoxml_path,
                    temp_dir=self.config.extraction.temp_directory,
                    timeout_seconds=self.config.extraction.timeout_seconds,
                    retry_attempts=self.config.extraction.retry_attempts,
                )

            self.rdf_converter = RDFConverter(
                oracle_home=self.config.oracle.home,
                db_connection=self.config.oracle.connection,
            )

        self.parser = CrystalParser()
        self.transformer = Transformer(
            formula_prefix=self.config.conversion.formula_prefix,
            parameter_prefix=self.config.conversion.parameter_prefix,
            field_prefix=self.config.conversion.field_prefix,
            on_unsupported_formula=self.config.conversion.on_unsupported_formula,
            on_complex_layout=self.config.conversion.on_complex_layout,
        )
        self.xml_generator = OracleXMLGenerator()

    def process_file(
        self,
        rpt_path: Path,
        output_path: Path,
    ) -> PipelineResult:
        """Process a single RPT file through the full pipeline.

        Args:
            rpt_path: Path to input RPT file.
            output_path: Path for output RDF file.

        Returns:
            PipelineResult with outcome.
        """
        self.logger.info(f"Processing: {rpt_path.name}")

        result = PipelineResult(
            rpt_path=rpt_path,
            rdf_path=None,
            status="failed",
        )

        # Stage 1: Extract RPT to XML
        extraction_result = self.extractor.extract(rpt_path)
        result.extraction_result = extraction_result

        if not extraction_result.success:
            result.errors.append(f"Extraction failed: {extraction_result.error.message}")
            return result

        # Stage 2: Parse XML to ReportModel
        try:
            report_model = self.parser.parse_file(
                extraction_result.xml_path,
                rpt_path,
            )
            result.report_model = report_model
        except Exception as e:
            result.errors.append(f"Parsing failed: {str(e)}")
            return result

        # Stage 3: Transform to Oracle format
        try:
            transformed = self.transformer.transform(report_model)
            result.transformed_report = transformed

            if not transformed.success:
                result.errors.extend(transformed.errors)
                # Continue anyway - partial conversion
        except Exception as e:
            result.errors.append(f"Transformation failed: {str(e)}")
            return result

        # Stage 4: Generate Oracle XML
        try:
            xml_path = output_path.with_suffix(".xml")
            self.xml_generator.generate_to_file(transformed, str(xml_path))
        except Exception as e:
            result.errors.append(f"XML generation failed: {str(e)}")
            return result

        # Stage 5: Convert XML to RDF (skip if skip_rdf is True)
        if self.skip_rdf:
            # When skipping RDF, the XML file is the final output
            result.rdf_path = xml_path

            # Determine final status based on transformation
            if transformed.elements_with_issues > 0:
                result.status = "partial"
                result.warnings.extend(transformed.warnings)
            else:
                result.status = "success"
        else:
            rdf_result = self.rdf_converter.convert(xml_path, output_path)
            result.rdf_result = rdf_result

            if rdf_result.success:
                result.rdf_path = output_path

                # Determine final status
                if transformed.elements_with_issues > 0:
                    result.status = "partial"
                    result.warnings.extend(transformed.warnings)
                else:
                    result.status = "success"
            else:
                result.errors.append(f"RDF conversion failed: {rdf_result.error.message}")

        return result

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        recursive: bool = True,
        workers: int = 4,
        progress_callback: Optional[Callable[[PipelineResult], None]] = None,
    ) -> ConversionReport:
        """Process all RPT files in a directory.

        Args:
            input_dir: Directory containing RPT files.
            output_dir: Directory for output RDF files.
            recursive: Whether to process subdirectories.
            workers: Number of parallel workers.
            progress_callback: Optional callback for progress updates.

        Returns:
            ConversionReport with batch results.
        """
        self.logger.info(f"Processing directory: {input_dir}")

        # Ensure output directory exists
        ensure_directory(output_dir)

        # Find all RPT files
        rpt_files = list(get_rpt_files(input_dir, recursive=recursive))
        self.logger.info(f"Found {len(rpt_files)} RPT files")

        if not rpt_files:
            return ConversionReport(total_files=0)

        # Initialize report
        report = ConversionReport(
            total_files=len(rpt_files),
            configuration={
                "input_dir": str(input_dir),
                "output_dir": str(output_dir),
                "workers": workers,
                "parallel": workers > 1,
            },
        )

        # Use parallel or sequential processing based on workers
        if workers > 1:
            self._process_parallel(
                rpt_files, input_dir, output_dir, workers,
                report, progress_callback
            )
        else:
            self._process_sequential(
                rpt_files, input_dir, output_dir,
                report, progress_callback
            )

        # Finalize report
        report.finalize()

        return report

    def _process_sequential(
        self,
        rpt_files: list[Path],
        input_dir: Path,
        output_dir: Path,
        report: ConversionReport,
        progress_callback: Optional[Callable[[PipelineResult], None]],
    ) -> None:
        """Process files sequentially (single worker)."""
        with ConversionProgressTracker(len(rpt_files)) as progress:
            for rpt_file in rpt_files:
                output_path = get_output_path(
                    rpt_file, input_dir, output_dir, new_extension=".rdf"
                )
                result = self.process_file(rpt_file, output_path)
                progress.update(result.status, rpt_file.name)
                self._record_result(result, report)

                if progress_callback:
                    progress_callback(result)

    def _process_parallel(
        self,
        rpt_files: list[Path],
        input_dir: Path,
        output_dir: Path,
        workers: int,
        report: ConversionReport,
        progress_callback: Optional[Callable[[PipelineResult], None]],
    ) -> None:
        """Process files in parallel using thread pool."""
        self.logger.info(f"Starting parallel processing with {workers} workers")

        # Thread-safe lock for updating report
        report_lock = Lock()

        def process_single(rpt_file: Path) -> PipelineResult:
            """Process a single file (runs in thread)."""
            output_path = get_output_path(
                rpt_file, input_dir, output_dir, new_extension=".rdf"
            )
            return self.process_file(rpt_file, output_path)

        with ConversionProgressTracker(
            len(rpt_files),
            description=f"Converting ({workers} workers)"
        ) as progress:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(process_single, rpt_file): rpt_file
                    for rpt_file in rpt_files
                }

                # Process completed tasks as they finish
                for future in as_completed(future_to_file):
                    rpt_file = future_to_file[future]
                    try:
                        result = future.result()

                        # Thread-safe update
                        with report_lock:
                            progress.update(result.status, rpt_file.name)
                            self._record_result(result, report)

                        if progress_callback:
                            progress_callback(result)

                    except Exception as e:
                        # Handle unexpected errors in thread
                        self.logger.error(f"Error processing {rpt_file}: {e}")
                        error_result = PipelineResult(
                            rpt_path=rpt_file,
                            rdf_path=None,
                            status="failed",
                            errors=[f"Thread error: {str(e)}"],
                        )

                        with report_lock:
                            progress.update("failed", rpt_file.name)
                            self._record_result(error_result, report)

                        if progress_callback:
                            progress_callback(error_result)

    def _record_result(self, result: PipelineResult, report: ConversionReport) -> None:
        """Record a pipeline result in the conversion report."""
        if result.status == "success":
            report.successful += 1
            report.successful_files.append(str(result.rpt_path))
        elif result.status == "partial":
            report.partial += 1
            report.partial_files.append(PartialConversion(
                file_name=str(result.rpt_path),
                rdf_path=str(result.rdf_path) if result.rdf_path else "",
                warnings=[ConversionError(
                    category=ErrorCategory.UNKNOWN_ERROR,
                    message=w,
                ) for w in result.warnings],
                elements_converted=result.transformed_report.elements_converted if result.transformed_report else 0,
                elements_with_issues=result.transformed_report.elements_with_issues if result.transformed_report else 0,
                completion_percentage=result.transformed_report.completion_percentage if result.transformed_report else 0,
            ))
        else:
            report.failed += 1
            report.failed_files.append(FailedConversion(
                file_name=str(result.rpt_path),
                errors=[ConversionError(
                    category=ErrorCategory.UNKNOWN_ERROR,
                    message=e,
                    is_fatal=True,
                ) for e in result.errors],
                stage_failed=self._determine_failed_stage(result),
            ))

    def _determine_failed_stage(self, result: PipelineResult) -> str:
        """Determine which stage failed based on result."""
        if result.extraction_result and not result.extraction_result.success:
            return "extraction"
        if result.report_model is None:
            return "parsing"
        if result.transformed_report is None:
            return "transformation"
        if result.rdf_result is None or not result.rdf_result.success:
            return "rdf_conversion"
        return "unknown"

    def validate_configuration(self) -> list[str]:
        """Validate pipeline configuration.

        Returns:
            List of validation errors.
        """
        errors = []

        # Validate config (skip RDF-related validation if skip_rdf is True)
        if not self.skip_rdf:
            errors.extend(self.config.validate())

        # Validate extractor setup
        if not self.use_mock:
            errors.extend(self.extractor.validate_setup())

        # Validate RDF converter setup (skip if skip_rdf is True)
        if not self.use_mock and not self.skip_rdf:
            errors.extend(self.rdf_converter.validate_setup())

        return errors

    def analyze_reports(
        self,
        input_dir: Path,
        recursive: bool = True,
    ) -> dict:
        """Analyze RPT files without converting.

        Args:
            input_dir: Directory containing RPT files.
            recursive: Whether to analyze subdirectories.

        Returns:
            Analysis summary.
        """
        self.logger.info(f"Analyzing directory: {input_dir}")

        rpt_files = list(get_rpt_files(input_dir, recursive=recursive))

        analysis = {
            "total_files": len(rpt_files),
            "complexity_distribution": {"simple": 0, "medium": 0, "complex": 0},
            "feature_usage": {
                "formulas": 0,
                "parameters": 0,
                "subreports": 0,
                "groups": 0,
            },
            "files": [],
        }

        for rpt_file in rpt_files:
            try:
                # Extract and parse
                extraction = self.extractor.extract(rpt_file)
                if not extraction.success:
                    continue

                model = self.parser.parse_file(extraction.xml_path, rpt_file)

                # Calculate complexity
                score = model.get_complexity_score()
                if score <= 3:
                    analysis["complexity_distribution"]["simple"] += 1
                elif score <= 6:
                    analysis["complexity_distribution"]["medium"] += 1
                else:
                    analysis["complexity_distribution"]["complex"] += 1

                # Track feature usage
                if model.formulas:
                    analysis["feature_usage"]["formulas"] += 1
                if model.parameters:
                    analysis["feature_usage"]["parameters"] += 1
                if model.subreports:
                    analysis["feature_usage"]["subreports"] += 1
                if model.groups:
                    analysis["feature_usage"]["groups"] += 1

                analysis["files"].append({
                    "name": rpt_file.name,
                    "complexity_score": score,
                    "formulas": len(model.formulas),
                    "parameters": len(model.parameters),
                    "subreports": len(model.subreports),
                    "groups": len(model.groups),
                })

            except Exception as e:
                self.logger.warning(f"Could not analyze {rpt_file.name}: {e}")

        return analysis
