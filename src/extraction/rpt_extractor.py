"""
RPT Extraction module for RPT to RDF Converter.

Extracts Crystal Reports RPT files to XML format using the RptToXml
command-line tool or Crystal Reports SDK.
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ..utils.logger import get_logger
from ..utils.error_handler import ErrorCategory, ConversionError


@dataclass
class ExtractionResult:
    """Result of extracting an RPT file to XML."""

    rpt_path: Path
    success: bool
    xml_path: Optional[Path] = None
    error: Optional[ConversionError] = None
    duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rpt_path": str(self.rpt_path),
            "success": self.success,
            "xml_path": str(self.xml_path) if self.xml_path else None,
            "error": self.error.to_dict() if self.error else None,
            "duration_seconds": self.duration_seconds,
        }


class RptExtractor:
    """Extracts Crystal Reports RPT files to XML format.

    Uses the RptToXml command-line tool to convert binary RPT files
    to human-readable XML that can be parsed for conversion.
    """

    def __init__(
        self,
        rpttoxml_path: str,
        temp_dir: str,
        timeout_seconds: int = 60,
        retry_attempts: int = 2,
    ):
        """Initialize the RPT extractor.

        Args:
            rpttoxml_path: Path to RptToXml executable.
            temp_dir: Directory for temporary files.
            timeout_seconds: Timeout for extraction process.
            retry_attempts: Number of retry attempts on failure.
        """
        self.rpttoxml_path = Path(rpttoxml_path)
        self.temp_dir = Path(temp_dir)
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.logger = get_logger("rpt_extractor")

        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate_setup(self) -> list[str]:
        """Validate that the extractor is properly configured.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if not self.rpttoxml_path.exists():
            errors.append(f"RptToXml executable not found: {self.rpttoxml_path}")

        if not self.temp_dir.exists():
            try:
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create temp directory: {e}")

        return errors

    def extract(self, rpt_file: Path) -> ExtractionResult:
        """Extract a single RPT file to XML.

        Args:
            rpt_file: Path to the RPT file.

        Returns:
            ExtractionResult with XML path or error information.
        """
        self.logger.info(f"Extracting: {rpt_file.name}")
        start_time = time.time()

        # Validate input file
        if not rpt_file.exists():
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"RPT file does not exist: {rpt_file}",
                    is_fatal=True,
                ),
                duration_seconds=time.time() - start_time,
            )

        # Determine output path
        xml_path = self.temp_dir / f"{rpt_file.stem}.xml"

        # Try extraction with retries
        last_error = None
        for attempt in range(self.retry_attempts + 1):
            if attempt > 0:
                self.logger.warning(f"Retry attempt {attempt} for {rpt_file.name}")
                time.sleep(1)  # Brief delay before retry

            try:
                result = self._run_rpttoxml(rpt_file, xml_path)

                if result.success:
                    self.logger.info(f"Extracted {rpt_file.name} in {result.duration_seconds:.2f}s")
                    return result

                last_error = result.error

            except Exception as e:
                last_error = ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"Unexpected error: {str(e)}",
                    is_fatal=True,
                )

        # All retries exhausted
        return ExtractionResult(
            rpt_path=rpt_file,
            success=False,
            error=last_error or ConversionError(
                category=ErrorCategory.EXTRACTION_FAILED,
                message="Extraction failed after all retries",
                is_fatal=True,
            ),
            duration_seconds=time.time() - start_time,
        )

    def _run_rpttoxml(self, rpt_file: Path, xml_path: Path) -> ExtractionResult:
        """Run the RptToXml command.

        Args:
            rpt_file: Path to input RPT file.
            xml_path: Path for output XML file.

        Returns:
            ExtractionResult with outcome.
        """
        start_time = time.time()

        # Build command
        # RptToXml.exe <input.rpt> [output.xml]
        cmd = [
            str(self.rpttoxml_path),
            str(rpt_file),
            str(xml_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=str(rpt_file.parent),
            )

            duration = time.time() - start_time

            # Check if XML was created
            if xml_path.exists() and xml_path.stat().st_size > 0:
                return ExtractionResult(
                    rpt_path=rpt_file,
                    success=True,
                    xml_path=xml_path,
                    duration_seconds=duration,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            # XML not created or empty - extraction failed
            error_msg = result.stderr or result.stdout or "No output produced"
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"RptToXml failed: {error_msg[:500]}",
                    is_fatal=True,
                    context={"return_code": result.returncode},
                ),
                duration_seconds=duration,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_TIMEOUT,
                    message=f"Extraction timed out after {self.timeout_seconds} seconds",
                    is_fatal=True,
                    suggested_fix="Try increasing the timeout or check if the file is corrupted",
                ),
                duration_seconds=self.timeout_seconds,
            )

        except FileNotFoundError:
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"RptToXml executable not found: {self.rpttoxml_path}",
                    is_fatal=True,
                    suggested_fix="Check rpttoxml_path in configuration",
                ),
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"Extraction error: {str(e)}",
                    is_fatal=True,
                ),
                duration_seconds=time.time() - start_time,
            )

    def batch_extract(
        self,
        rpt_files: list[Path],
        workers: int = 4,
        progress_callback: Optional[Callable[[ExtractionResult], None]] = None,
    ) -> list[ExtractionResult]:
        """Extract multiple RPT files in parallel.

        Args:
            rpt_files: List of RPT file paths.
            workers: Number of parallel workers.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of ExtractionResults.
        """
        self.logger.info(f"Starting batch extraction of {len(rpt_files)} files with {workers} workers")
        results: list[ExtractionResult] = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all extraction tasks
            future_to_file = {
                executor.submit(self.extract, rpt_file): rpt_file
                for rpt_file in rpt_files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                rpt_file = future_to_file[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = ExtractionResult(
                        rpt_path=rpt_file,
                        success=False,
                        error=ConversionError(
                            category=ErrorCategory.EXTRACTION_FAILED,
                            message=f"Worker exception: {str(e)}",
                            is_fatal=True,
                        ),
                    )

                results.append(result)

                if progress_callback:
                    progress_callback(result)

        # Sort results to match input order
        path_to_result = {str(r.rpt_path): r for r in results}
        ordered_results = [path_to_result[str(f)] for f in rpt_files]

        successful = sum(1 for r in ordered_results if r.success)
        self.logger.info(f"Batch extraction complete: {successful}/{len(rpt_files)} successful")

        return ordered_results

    def cleanup_temp_files(self, keep_xml: bool = False) -> int:
        """Clean up temporary files.

        Args:
            keep_xml: If True, keep XML files (only clean other temp files).

        Returns:
            Number of files removed.
        """
        if not self.temp_dir.exists():
            return 0

        count = 0
        patterns = ["*.tmp", "*.log"] if keep_xml else ["*.xml", "*.tmp", "*.log"]

        for pattern in patterns:
            for file_path in self.temp_dir.glob(pattern):
                try:
                    file_path.unlink()
                    count += 1
                except OSError:
                    pass

        return count


class MockRptExtractor(RptExtractor):
    """Mock extractor for testing without Crystal Reports runtime.

    Creates sample XML output for testing the rest of the pipeline.
    """

    def _run_rpttoxml(self, rpt_file: Path, xml_path: Path) -> ExtractionResult:
        """Generate mock XML output."""
        start_time = time.time()

        # Generate sample Crystal Reports XML
        sample_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CrystalReport Name="{rpt_file.stem}">
    <DatabaseInfo>
        <Table Name="Sample_Table">
            <Field Name="ID" Type="Number"/>
            <Field Name="Name" Type="String"/>
            <Field Name="Date" Type="Date"/>
        </Table>
    </DatabaseInfo>
    <Formulas>
        <Formula Name="SampleFormula">
            <Text>{{Sample_Table.Name}} &amp; " - " &amp; ToText({{Sample_Table.ID}})</Text>
        </Formula>
    </Formulas>
    <Parameters>
        <Parameter Name="StartDate" Type="Date"/>
    </Parameters>
    <Sections>
        <Section Type="ReportHeader" Height="500">
            <Field Name="F_Title" Source="Title" X="100" Y="100" Width="300" Height="50"/>
        </Section>
        <Section Type="Detail" Height="200">
            <Field Name="F_ID" Source="Sample_Table.ID" X="100" Y="10" Width="100" Height="20"/>
            <Field Name="F_Name" Source="Sample_Table.Name" X="200" Y="10" Width="200" Height="20"/>
        </Section>
    </Sections>
</CrystalReport>
"""

        try:
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(sample_xml)

            return ExtractionResult(
                rpt_path=rpt_file,
                success=True,
                xml_path=xml_path,
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return ExtractionResult(
                rpt_path=rpt_file,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"Mock extraction failed: {str(e)}",
                    is_fatal=True,
                ),
                duration_seconds=time.time() - start_time,
            )
