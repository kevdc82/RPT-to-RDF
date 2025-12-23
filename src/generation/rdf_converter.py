"""
RDF Converter for RPT to RDF Converter.

Wraps Oracle's rwconverter utility to convert XML to binary RDF format.
"""

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..utils.error_handler import ConversionError, ErrorCategory
from ..utils.logger import get_logger


@dataclass
class ConversionResult:
    """Result of converting XML to RDF."""

    xml_path: Path
    rdf_path: Path
    success: bool
    error: Optional[ConversionError] = None
    duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "xml_path": str(self.xml_path),
            "rdf_path": str(self.rdf_path),
            "success": self.success,
            "error": self.error.to_dict() if self.error else None,
            "duration_seconds": self.duration_seconds,
        }


class RDFConverter:
    """Converts Oracle Reports XML to binary RDF format using rwconverter."""

    def __init__(
        self,
        oracle_home: str,
        db_connection: str,
        timeout_seconds: int = 120,
    ):
        """Initialize the RDF converter.

        Args:
            oracle_home: Path to Oracle home directory.
            db_connection: Database connection string (user/password@database).
            timeout_seconds: Timeout for conversion process.
        """
        self.oracle_home = Path(oracle_home)
        self.db_connection = db_connection
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger("rdf_converter")

        # Determine rwconverter path
        if (self.oracle_home / "bin" / "rwconverter.exe").exists():
            self.rwconverter = self.oracle_home / "bin" / "rwconverter.exe"
        elif (self.oracle_home / "bin" / "rwconverter").exists():
            self.rwconverter = self.oracle_home / "bin" / "rwconverter"
        else:
            self.rwconverter = self.oracle_home / "bin" / "rwconverter"

    def validate_setup(self) -> list[str]:
        """Validate that rwconverter is properly configured.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if not self.oracle_home.exists():
            errors.append(f"Oracle home does not exist: {self.oracle_home}")
            return errors

        if not self.rwconverter.exists():
            errors.append(f"rwconverter not found: {self.rwconverter}")

        if not self.db_connection:
            errors.append("Database connection string is required")

        return errors

    def convert(self, xml_path: Path, rdf_path: Path) -> ConversionResult:
        """Convert XML to RDF format.

        Args:
            xml_path: Path to input XML file.
            rdf_path: Path for output RDF file.

        Returns:
            ConversionResult with outcome.
        """
        self.logger.info(f"Converting: {xml_path.name} -> {rdf_path.name}")
        start_time = time.time()

        # Validate input
        if not xml_path.exists():
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"XML file does not exist: {xml_path}",
                    is_fatal=True,
                ),
                duration_seconds=time.time() - start_time,
            )

        # Ensure output directory exists
        rdf_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            str(self.rwconverter),
            f"userid={self.db_connection}",
            "stype=xmlfile",
            f"source={xml_path}",
            "dtype=rdffile",
            f"dest={rdf_path}",
            "batch=yes",
            "overwrite=yes",
        ]

        try:
            # Set environment for Oracle
            env = self._get_oracle_env()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
                cwd=str(xml_path.parent),
            )

            duration = time.time() - start_time

            # Check if RDF was created
            if rdf_path.exists() and rdf_path.stat().st_size > 0:
                self.logger.info(f"Converted {xml_path.name} in {duration:.2f}s")
                return ConversionResult(
                    xml_path=xml_path,
                    rdf_path=rdf_path,
                    success=True,
                    duration_seconds=duration,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            # Conversion failed
            error_msg = result.stderr or result.stdout or "rwconverter produced no output"
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RWCONVERTER_ERROR,
                    message=f"rwconverter failed: {error_msg[:500]}",
                    is_fatal=True,
                    context={"return_code": result.returncode},
                ),
                duration_seconds=duration,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RWCONVERTER_TIMEOUT,
                    message=f"rwconverter timed out after {self.timeout_seconds} seconds",
                    is_fatal=True,
                    suggested_fix="Increase timeout or check for issues with the XML",
                ),
                duration_seconds=self.timeout_seconds,
            )

        except FileNotFoundError:
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RWCONVERTER_ERROR,
                    message=f"rwconverter not found: {self.rwconverter}",
                    is_fatal=True,
                    suggested_fix="Verify ORACLE_HOME is set correctly",
                ),
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"Unexpected error: {str(e)}",
                    is_fatal=True,
                ),
                duration_seconds=time.time() - start_time,
            )

    def batch_convert(
        self,
        conversions: list[tuple[Path, Path]],
    ) -> list[ConversionResult]:
        """Convert multiple XML files to RDF.

        rwconverter supports batch conversion with multiple source/dest files.

        Args:
            conversions: List of (xml_path, rdf_path) tuples.

        Returns:
            List of ConversionResults.
        """
        if len(conversions) == 0:
            return []

        # For small batches, convert individually
        if len(conversions) <= 5:
            return [self.convert(xml, rdf) for xml, rdf in conversions]

        # For larger batches, use rwconverter's batch capability
        self.logger.info(f"Batch converting {len(conversions)} files")
        start_time = time.time()

        # Format file lists
        xml_files = [str(xml) for xml, _ in conversions]
        rdf_files = [str(rdf) for _, rdf in conversions]

        source_list = '("' + '", "'.join(xml_files) + '")'
        dest_list = '("' + '", "'.join(rdf_files) + '")'

        cmd = [
            str(self.rwconverter),
            f"userid={self.db_connection}",
            "stype=xmlfile",
            f"source={source_list}",
            "dtype=rdffile",
            f"dest={dest_list}",
            "batch=yes",
            "overwrite=yes",
        ]

        try:
            env = self._get_oracle_env()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds * len(conversions),
                env=env,
            )

            # Build individual results
            results = []
            for xml_path, rdf_path in conversions:
                if rdf_path.exists() and rdf_path.stat().st_size > 0:
                    results.append(
                        ConversionResult(
                            xml_path=xml_path,
                            rdf_path=rdf_path,
                            success=True,
                            duration_seconds=(time.time() - start_time) / len(conversions),
                        )
                    )
                else:
                    results.append(
                        ConversionResult(
                            xml_path=xml_path,
                            rdf_path=rdf_path,
                            success=False,
                            error=ConversionError(
                                category=ErrorCategory.RDF_CONVERSION_FAILED,
                                message="RDF file not created in batch conversion",
                                is_fatal=True,
                            ),
                        )
                    )

            return results

        except Exception as e:
            # On batch failure, try individual conversions
            self.logger.warning(f"Batch conversion failed: {e}, falling back to individual")
            return [self.convert(xml, rdf) for xml, rdf in conversions]

    def _get_oracle_env(self) -> dict:
        """Get environment variables for Oracle."""
        import os

        env = os.environ.copy()
        env["ORACLE_HOME"] = str(self.oracle_home)
        env["PATH"] = f"{self.oracle_home / 'bin'};{env.get('PATH', '')}"
        return env


class MockRDFConverter(RDFConverter):
    """Mock converter for testing without Oracle Reports installed."""

    def convert(self, xml_path: Path, rdf_path: Path) -> ConversionResult:
        """Create a mock RDF file."""
        start_time = time.time()

        if not xml_path.exists():
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"XML file does not exist: {xml_path}",
                    is_fatal=True,
                ),
            )

        # Create mock RDF (just copy XML for testing)
        rdf_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create a simple mock RDF header + XML content
            with open(xml_path, "rb") as f:
                xml_content = f.read()

            # Mock RDF header (not real RDF format, just for testing)
            rdf_header = b"MOCK_RDF_FILE\x00\x00\x00\x00"

            with open(rdf_path, "wb") as f:
                f.write(rdf_header)
                f.write(xml_content)

            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=True,
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return ConversionResult(
                xml_path=xml_path,
                rdf_path=rdf_path,
                success=False,
                error=ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"Mock conversion failed: {e}",
                    is_fatal=True,
                ),
            )
