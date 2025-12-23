"""
Output comparison utilities for RPT to RDF Converter.

Provides tools for comparing Crystal Reports and Oracle Reports output
to validate conversion accuracy. Supports:
- PDF visual comparison (pixel-based and structural)
- CSV data comparison (row/column matching)
- Report data validation

These utilities help verify that converted Oracle Reports produce
equivalent output to the original Crystal Reports.
"""

import csv
import hashlib
import io
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ComparisonResult(Enum):
    """Result of a comparison operation."""
    IDENTICAL = "identical"
    SIMILAR = "similar"  # Within acceptable threshold
    DIFFERENT = "different"
    ERROR = "error"
    SKIPPED = "skipped"


class DifferenceType(Enum):
    """Types of differences found during comparison."""
    MISSING_ROW = "missing_row"
    EXTRA_ROW = "extra_row"
    VALUE_MISMATCH = "value_mismatch"
    COLUMN_MISMATCH = "column_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    FORMAT_DIFFERENCE = "format_difference"
    LAYOUT_DIFFERENCE = "layout_difference"
    VISUAL_DIFFERENCE = "visual_difference"


@dataclass
class Difference:
    """Represents a single difference between two outputs."""
    diff_type: DifferenceType
    location: str  # Row/column, page number, or coordinate
    expected: Any
    actual: Any
    severity: str = "warning"  # info, warning, error
    details: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.diff_type.value,
            "location": self.location,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class ComparisonReport:
    """Report of comparison results between two outputs."""
    source_file: str
    target_file: str
    comparison_type: str  # csv, pdf, data
    result: ComparisonResult = ComparisonResult.SKIPPED
    differences: list[Difference] = field(default_factory=list)
    similarity_score: float = 0.0  # 0.0 to 100.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "comparison_type": self.comparison_type,
            "result": self.result.value,
            "differences_count": len(self.differences),
            "differences": [d.to_dict() for d in self.differences[:100]],  # Limit to first 100
            "similarity_score": self.similarity_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "error_message": self.error_message,
        }

    @property
    def is_acceptable(self) -> bool:
        """Check if comparison result is acceptable (identical or similar)."""
        return self.result in (ComparisonResult.IDENTICAL, ComparisonResult.SIMILAR)


class CSVComparator:
    """Compares CSV data outputs from Crystal and Oracle Reports."""

    def __init__(
        self,
        tolerance: float = 0.001,
        ignore_case: bool = True,
        ignore_whitespace: bool = True,
        date_formats: Optional[list[str]] = None,
    ):
        """Initialize CSV comparator.

        Args:
            tolerance: Numeric tolerance for floating-point comparison.
            ignore_case: Whether to ignore case in string comparison.
            ignore_whitespace: Whether to ignore leading/trailing whitespace.
            date_formats: List of date formats to try when parsing dates.
        """
        self.tolerance = tolerance
        self.ignore_case = ignore_case
        self.ignore_whitespace = ignore_whitespace
        self.date_formats = date_formats or [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
        ]

    def compare(
        self,
        source_path: Path,
        target_path: Path,
        key_columns: Optional[list[str]] = None,
    ) -> ComparisonReport:
        """Compare two CSV files.

        Args:
            source_path: Path to source (Crystal) CSV file.
            target_path: Path to target (Oracle) CSV file.
            key_columns: Column names to use as keys for row matching.

        Returns:
            ComparisonReport with results.
        """
        report = ComparisonReport(
            source_file=str(source_path),
            target_file=str(target_path),
            comparison_type="csv",
        )

        try:
            source_data = self._read_csv(source_path)
            target_data = self._read_csv(target_path)
        except Exception as e:
            report.result = ComparisonResult.ERROR
            report.error_message = f"Failed to read CSV files: {e}"
            return report

        # Compare headers
        source_headers = source_data.get("headers", [])
        target_headers = target_data.get("headers", [])

        if not self._compare_headers(source_headers, target_headers, report):
            # Headers don't match, but continue to compare data
            pass

        # Compare rows
        source_rows = source_data.get("rows", [])
        target_rows = target_data.get("rows", [])

        report.metadata["source_row_count"] = len(source_rows)
        report.metadata["target_row_count"] = len(target_rows)
        report.metadata["source_column_count"] = len(source_headers)
        report.metadata["target_column_count"] = len(target_headers)

        if key_columns:
            self._compare_rows_by_key(source_rows, target_rows, key_columns, source_headers, report)
        else:
            self._compare_rows_by_position(source_rows, target_rows, source_headers, report)

        # Calculate similarity score
        total_cells = len(source_rows) * len(source_headers) if source_rows else 1
        matching_cells = total_cells - sum(
            1 for d in report.differences if d.diff_type == DifferenceType.VALUE_MISMATCH
        )
        report.similarity_score = (matching_cells / total_cells) * 100 if total_cells > 0 else 100.0

        # Determine overall result
        if not report.differences:
            report.result = ComparisonResult.IDENTICAL
        elif report.similarity_score >= 95.0:
            report.result = ComparisonResult.SIMILAR
        else:
            report.result = ComparisonResult.DIFFERENT

        return report

    def _read_csv(self, path: Path) -> dict[str, Any]:
        """Read CSV file and return structured data."""
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            # Try to detect dialect
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(f, dialect=dialect)
            headers = reader.fieldnames or []
            rows = list(reader)

        return {"headers": headers, "rows": rows}

    def _compare_headers(
        self,
        source: list[str],
        target: list[str],
        report: ComparisonReport,
    ) -> bool:
        """Compare CSV headers and add differences to report."""
        source_set = set(self._normalize_string(h) for h in source)
        target_set = set(self._normalize_string(h) for h in target)

        missing = source_set - target_set
        extra = target_set - source_set

        for col in missing:
            report.differences.append(Difference(
                diff_type=DifferenceType.COLUMN_MISMATCH,
                location="headers",
                expected=col,
                actual="(missing)",
                severity="error",
                details=f"Column '{col}' exists in source but not in target",
            ))

        for col in extra:
            report.differences.append(Difference(
                diff_type=DifferenceType.COLUMN_MISMATCH,
                location="headers",
                expected="(not present)",
                actual=col,
                severity="warning",
                details=f"Column '{col}' exists in target but not in source",
            ))

        return len(missing) == 0 and len(extra) == 0

    def _compare_rows_by_position(
        self,
        source_rows: list[dict],
        target_rows: list[dict],
        headers: list[str],
        report: ComparisonReport,
    ) -> None:
        """Compare rows by their position in the file."""
        max_rows = max(len(source_rows), len(target_rows))

        for i in range(max_rows):
            if i >= len(source_rows):
                report.differences.append(Difference(
                    diff_type=DifferenceType.EXTRA_ROW,
                    location=f"row {i + 1}",
                    expected="(no row)",
                    actual=str(target_rows[i]),
                    severity="warning",
                ))
                continue

            if i >= len(target_rows):
                report.differences.append(Difference(
                    diff_type=DifferenceType.MISSING_ROW,
                    location=f"row {i + 1}",
                    expected=str(source_rows[i]),
                    actual="(no row)",
                    severity="error",
                ))
                continue

            # Compare cell values
            for col in headers:
                source_val = source_rows[i].get(col, "")
                target_val = target_rows[i].get(col, "")

                if not self._values_equal(source_val, target_val):
                    report.differences.append(Difference(
                        diff_type=DifferenceType.VALUE_MISMATCH,
                        location=f"row {i + 1}, column '{col}'",
                        expected=source_val,
                        actual=target_val,
                        severity="warning",
                    ))

    def _compare_rows_by_key(
        self,
        source_rows: list[dict],
        target_rows: list[dict],
        key_columns: list[str],
        headers: list[str],
        report: ComparisonReport,
    ) -> None:
        """Compare rows by key columns (for unordered comparison)."""
        def make_key(row: dict) -> tuple:
            return tuple(self._normalize_string(str(row.get(k, ""))) for k in key_columns)

        source_by_key = {make_key(row): row for row in source_rows}
        target_by_key = {make_key(row): row for row in target_rows}

        # Find missing and extra rows
        missing_keys = set(source_by_key.keys()) - set(target_by_key.keys())
        extra_keys = set(target_by_key.keys()) - set(source_by_key.keys())

        for key in missing_keys:
            report.differences.append(Difference(
                diff_type=DifferenceType.MISSING_ROW,
                location=f"key={key}",
                expected=str(source_by_key[key]),
                actual="(not found)",
                severity="error",
            ))

        for key in extra_keys:
            report.differences.append(Difference(
                diff_type=DifferenceType.EXTRA_ROW,
                location=f"key={key}",
                expected="(not found)",
                actual=str(target_by_key[key]),
                severity="warning",
            ))

        # Compare matching rows
        common_keys = set(source_by_key.keys()) & set(target_by_key.keys())
        for key in common_keys:
            source_row = source_by_key[key]
            target_row = target_by_key[key]

            for col in headers:
                if col in key_columns:
                    continue  # Skip key columns

                source_val = source_row.get(col, "")
                target_val = target_row.get(col, "")

                if not self._values_equal(source_val, target_val):
                    report.differences.append(Difference(
                        diff_type=DifferenceType.VALUE_MISMATCH,
                        location=f"key={key}, column '{col}'",
                        expected=source_val,
                        actual=target_val,
                        severity="warning",
                    ))

    def _normalize_string(self, value: str) -> str:
        """Normalize a string value for comparison."""
        if self.ignore_whitespace:
            value = value.strip()
        if self.ignore_case:
            value = value.lower()
        return value

    def _values_equal(self, source: str, target: str) -> bool:
        """Check if two values are equal within tolerance."""
        # Normalize strings
        source_norm = self._normalize_string(str(source))
        target_norm = self._normalize_string(str(target))

        # Exact string match
        if source_norm == target_norm:
            return True

        # Try numeric comparison
        try:
            source_num = float(source_norm.replace(",", ""))
            target_num = float(target_norm.replace(",", ""))
            return abs(source_num - target_num) <= self.tolerance
        except ValueError:
            pass

        # Try date comparison
        source_date = self._parse_date(source_norm)
        target_date = self._parse_date(target_norm)
        if source_date and target_date:
            return source_date == target_date

        return False

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Try to parse a date string."""
        for fmt in self.date_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None


class PDFComparator:
    """Compares PDF outputs from Crystal and Oracle Reports.

    Requires external tools:
    - pdf2image (Python library) or pdftoppm (poppler-utils)
    - Pillow (PIL) for image comparison

    Falls back to file hash comparison if image tools unavailable.
    """

    def __init__(
        self,
        similarity_threshold: float = 95.0,
        dpi: int = 150,
        use_structural: bool = True,
    ):
        """Initialize PDF comparator.

        Args:
            similarity_threshold: Percentage threshold for "similar" result.
            dpi: DPI for PDF to image conversion.
            use_structural: Use structural comparison (text extraction) as fallback.
        """
        self.similarity_threshold = similarity_threshold
        self.dpi = dpi
        self.use_structural = use_structural
        self._check_dependencies()

    def _check_dependencies(self) -> dict[str, bool]:
        """Check available comparison methods."""
        self.available_methods = {
            "pillow": False,
            "pdf2image": False,
            "pdftoppm": False,
            "pdftotext": False,
        }

        try:
            from PIL import Image
            self.available_methods["pillow"] = True
        except ImportError:
            pass

        try:
            import pdf2image
            self.available_methods["pdf2image"] = True
        except ImportError:
            pass

        # Check for poppler tools
        try:
            result = subprocess.run(
                ["pdftoppm", "-v"],
                capture_output=True,
                timeout=5,
            )
            self.available_methods["pdftoppm"] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        try:
            result = subprocess.run(
                ["pdftotext", "-v"],
                capture_output=True,
                timeout=5,
            )
            self.available_methods["pdftotext"] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return self.available_methods

    def compare(
        self,
        source_path: Path,
        target_path: Path,
        pages: Optional[list[int]] = None,
    ) -> ComparisonReport:
        """Compare two PDF files.

        Args:
            source_path: Path to source (Crystal) PDF file.
            target_path: Path to target (Oracle) PDF file.
            pages: Specific pages to compare (1-indexed), or None for all.

        Returns:
            ComparisonReport with results.
        """
        report = ComparisonReport(
            source_file=str(source_path),
            target_file=str(target_path),
            comparison_type="pdf",
        )

        if not source_path.exists():
            report.result = ComparisonResult.ERROR
            report.error_message = f"Source file not found: {source_path}"
            return report

        if not target_path.exists():
            report.result = ComparisonResult.ERROR
            report.error_message = f"Target file not found: {target_path}"
            return report

        # Try visual comparison first
        if self.available_methods["pdf2image"] and self.available_methods["pillow"]:
            return self._compare_visual(source_path, target_path, pages, report)

        # Fall back to structural comparison
        if self.use_structural and self.available_methods["pdftotext"]:
            return self._compare_structural(source_path, target_path, report)

        # Fall back to hash comparison
        return self._compare_hash(source_path, target_path, report)

    def _compare_visual(
        self,
        source_path: Path,
        target_path: Path,
        pages: Optional[list[int]],
        report: ComparisonReport,
    ) -> ComparisonReport:
        """Compare PDFs by converting to images and comparing pixels."""
        try:
            from pdf2image import convert_from_path
            from PIL import Image, ImageChops
            import math

            source_images = convert_from_path(str(source_path), dpi=self.dpi)
            target_images = convert_from_path(str(target_path), dpi=self.dpi)

            report.metadata["source_page_count"] = len(source_images)
            report.metadata["target_page_count"] = len(target_images)

            if len(source_images) != len(target_images):
                report.differences.append(Difference(
                    diff_type=DifferenceType.LAYOUT_DIFFERENCE,
                    location="document",
                    expected=f"{len(source_images)} pages",
                    actual=f"{len(target_images)} pages",
                    severity="warning",
                ))

            # Compare each page
            page_scores = []
            pages_to_compare = pages or list(range(1, min(len(source_images), len(target_images)) + 1))

            for page_num in pages_to_compare:
                idx = page_num - 1
                if idx >= len(source_images) or idx >= len(target_images):
                    continue

                source_img = source_images[idx]
                target_img = target_images[idx]

                # Resize if dimensions differ
                if source_img.size != target_img.size:
                    target_img = target_img.resize(source_img.size, Image.Resampling.LANCZOS)
                    report.differences.append(Difference(
                        diff_type=DifferenceType.LAYOUT_DIFFERENCE,
                        location=f"page {page_num}",
                        expected=f"size {source_img.size}",
                        actual=f"size {target_images[idx].size}",
                        severity="info",
                    ))

                # Calculate similarity
                diff = ImageChops.difference(source_img.convert("RGB"), target_img.convert("RGB"))
                diff_data = list(diff.getdata())

                # Calculate RMS difference
                total_pixels = len(diff_data)
                sum_sq = sum(sum(c**2 for c in pixel) / 3 for pixel in diff_data)
                rms = math.sqrt(sum_sq / total_pixels) if total_pixels > 0 else 0

                # Convert RMS to similarity percentage (255 is max difference per channel)
                page_similarity = max(0, 100 - (rms / 255 * 100))
                page_scores.append(page_similarity)

                if page_similarity < self.similarity_threshold:
                    report.differences.append(Difference(
                        diff_type=DifferenceType.VISUAL_DIFFERENCE,
                        location=f"page {page_num}",
                        expected="visual match",
                        actual=f"{page_similarity:.1f}% similar",
                        severity="warning" if page_similarity >= 80 else "error",
                    ))

            # Overall similarity
            report.similarity_score = sum(page_scores) / len(page_scores) if page_scores else 0

            if report.similarity_score >= 99.0 and not any(
                d for d in report.differences if d.severity == "error"
            ):
                report.result = ComparisonResult.IDENTICAL
            elif report.similarity_score >= self.similarity_threshold:
                report.result = ComparisonResult.SIMILAR
            else:
                report.result = ComparisonResult.DIFFERENT

        except Exception as e:
            report.result = ComparisonResult.ERROR
            report.error_message = f"Visual comparison failed: {e}"

        return report

    def _compare_structural(
        self,
        source_path: Path,
        target_path: Path,
        report: ComparisonReport,
    ) -> ComparisonReport:
        """Compare PDFs by extracting and comparing text content."""
        try:
            source_text = self._extract_text(source_path)
            target_text = self._extract_text(target_path)

            report.metadata["source_char_count"] = len(source_text)
            report.metadata["target_char_count"] = len(target_text)
            report.metadata["comparison_method"] = "structural"

            # Simple similarity based on common content
            source_words = set(source_text.lower().split())
            target_words = set(target_text.lower().split())

            common = source_words & target_words
            total = source_words | target_words

            report.similarity_score = (len(common) / len(total) * 100) if total else 100.0

            if source_text.strip() == target_text.strip():
                report.result = ComparisonResult.IDENTICAL
            elif report.similarity_score >= self.similarity_threshold:
                report.result = ComparisonResult.SIMILAR
            else:
                report.result = ComparisonResult.DIFFERENT
                report.differences.append(Difference(
                    diff_type=DifferenceType.VALUE_MISMATCH,
                    location="document text",
                    expected=f"{len(source_words)} unique words",
                    actual=f"{len(target_words)} unique words",
                    severity="warning",
                ))

        except Exception as e:
            report.result = ComparisonResult.ERROR
            report.error_message = f"Structural comparison failed: {e}"

        return report

    def _compare_hash(
        self,
        source_path: Path,
        target_path: Path,
        report: ComparisonReport,
    ) -> ComparisonReport:
        """Compare PDFs by file hash (exact match only)."""
        try:
            source_hash = self._file_hash(source_path)
            target_hash = self._file_hash(target_path)

            report.metadata["source_hash"] = source_hash
            report.metadata["target_hash"] = target_hash
            report.metadata["comparison_method"] = "hash"

            if source_hash == target_hash:
                report.result = ComparisonResult.IDENTICAL
                report.similarity_score = 100.0
            else:
                report.result = ComparisonResult.DIFFERENT
                report.similarity_score = 0.0
                report.differences.append(Difference(
                    diff_type=DifferenceType.VALUE_MISMATCH,
                    location="file hash",
                    expected=source_hash[:16] + "...",
                    actual=target_hash[:16] + "...",
                    severity="info",
                    details="Files differ; install pdf2image/Pillow for detailed comparison",
                ))

        except Exception as e:
            report.result = ComparisonResult.ERROR
            report.error_message = f"Hash comparison failed: {e}"

        return report

    def _extract_text(self, path: Path) -> str:
        """Extract text from PDF using pdftotext."""
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout

    def _file_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class OutputValidator:
    """Orchestrates output comparison and validation.

    Coordinates CSV and PDF comparison to provide comprehensive
    validation of converted reports.
    """

    def __init__(
        self,
        csv_tolerance: float = 0.001,
        pdf_similarity_threshold: float = 95.0,
    ):
        """Initialize output validator.

        Args:
            csv_tolerance: Numeric tolerance for CSV comparison.
            pdf_similarity_threshold: Similarity threshold for PDF comparison.
        """
        self.csv_comparator = CSVComparator(tolerance=csv_tolerance)
        self.pdf_comparator = PDFComparator(similarity_threshold=pdf_similarity_threshold)

    def validate_conversion(
        self,
        crystal_csv: Optional[Path] = None,
        oracle_csv: Optional[Path] = None,
        crystal_pdf: Optional[Path] = None,
        oracle_pdf: Optional[Path] = None,
        key_columns: Optional[list[str]] = None,
    ) -> dict[str, ComparisonReport]:
        """Validate a conversion by comparing outputs.

        Args:
            crystal_csv: Path to Crystal Reports CSV output.
            oracle_csv: Path to Oracle Reports CSV output.
            crystal_pdf: Path to Crystal Reports PDF output.
            oracle_pdf: Path to Oracle Reports PDF output.
            key_columns: Key columns for CSV row matching.

        Returns:
            Dictionary of comparison reports by type.
        """
        results = {}

        # Compare CSV data
        if crystal_csv and oracle_csv:
            results["csv"] = self.csv_comparator.compare(
                crystal_csv,
                oracle_csv,
                key_columns=key_columns,
            )

        # Compare PDF output
        if crystal_pdf and oracle_pdf:
            results["pdf"] = self.pdf_comparator.compare(
                crystal_pdf,
                oracle_pdf,
            )

        return results

    def generate_validation_report(
        self,
        report_name: str,
        comparisons: dict[str, ComparisonReport],
        output_dir: Path,
    ) -> Path:
        """Generate a comprehensive validation report.

        Args:
            report_name: Name of the report being validated.
            comparisons: Dictionary of comparison reports.
            output_dir: Directory to save the report.

        Returns:
            Path to the generated HTML report.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"validation_{report_name}_{timestamp}.html"

        # Determine overall status
        all_acceptable = all(r.is_acceptable for r in comparisons.values())
        overall_status = "PASS" if all_acceptable else "FAIL"
        status_class = "success" if all_acceptable else "failed"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Validation Report: {report_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px; margin: 0 auto; background: white;
            padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; }}
        .status {{ padding: 10px 20px; border-radius: 4px; display: inline-block; font-weight: bold; }}
        .status.success {{ background: #d4edda; color: #155724; }}
        .status.failed {{ background: #f8d7da; color: #721c24; }}
        .comparison {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .comparison h3 {{ margin-top: 0; }}
        .similarity {{ font-size: 24px; font-weight: bold; }}
        .similarity.high {{ color: #28a745; }}
        .similarity.medium {{ color: #ffc107; }}
        .similarity.low {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .diff-error {{ color: #dc3545; }}
        .diff-warning {{ color: #ffc107; }}
        .diff-info {{ color: #17a2b8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Validation Report</h1>
        <p><strong>Report:</strong> {report_name}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Overall Status:</strong> <span class="status {status_class}">{overall_status}</span></p>
"""

        for comp_type, report in comparisons.items():
            sim_class = "high" if report.similarity_score >= 95 else ("medium" if report.similarity_score >= 80 else "low")
            html += f"""
        <div class="comparison">
            <h3>{comp_type.upper()} Comparison</h3>
            <p><strong>Result:</strong> {report.result.value}</p>
            <p><strong>Similarity:</strong> <span class="similarity {sim_class}">{report.similarity_score:.1f}%</span></p>
            <p><strong>Source:</strong> {report.source_file}</p>
            <p><strong>Target:</strong> {report.target_file}</p>
"""

            if report.differences:
                html += """
            <h4>Differences ({count})</h4>
            <table>
                <tr><th>Type</th><th>Location</th><th>Expected</th><th>Actual</th><th>Severity</th></tr>
""".format(count=len(report.differences))

                for diff in report.differences[:20]:  # Show first 20
                    html += f"""
                <tr>
                    <td>{diff.diff_type.value}</td>
                    <td>{diff.location}</td>
                    <td>{diff.expected[:50] if diff.expected else ''}</td>
                    <td>{diff.actual[:50] if diff.actual else ''}</td>
                    <td class="diff-{diff.severity}">{diff.severity}</td>
                </tr>
"""

                if len(report.differences) > 20:
                    html += f"""
                <tr><td colspan="5">... and {len(report.differences) - 20} more differences</td></tr>
"""

                html += """            </table>
"""

            if report.error_message:
                html += f"""
            <p style="color: #dc3545;"><strong>Error:</strong> {report.error_message}</p>
"""

            html += """        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return report_path

    def batch_validate(
        self,
        validations: list[dict],
        output_dir: Path,
    ) -> list[dict[str, Any]]:
        """Validate multiple report conversions.

        Args:
            validations: List of validation configs, each with:
                - name: Report name
                - crystal_csv: Path to Crystal CSV (optional)
                - oracle_csv: Path to Oracle CSV (optional)
                - crystal_pdf: Path to Crystal PDF (optional)
                - oracle_pdf: Path to Oracle PDF (optional)
                - key_columns: Key columns for CSV matching (optional)
            output_dir: Directory to save reports.

        Returns:
            List of validation results.
        """
        results = []

        for config in validations:
            name = config.get("name", "unknown")
            comparisons = self.validate_conversion(
                crystal_csv=Path(config["crystal_csv"]) if config.get("crystal_csv") else None,
                oracle_csv=Path(config["oracle_csv"]) if config.get("oracle_csv") else None,
                crystal_pdf=Path(config["crystal_pdf"]) if config.get("crystal_pdf") else None,
                oracle_pdf=Path(config["oracle_pdf"]) if config.get("oracle_pdf") else None,
                key_columns=config.get("key_columns"),
            )

            report_path = self.generate_validation_report(name, comparisons, output_dir)

            results.append({
                "name": name,
                "report_path": str(report_path),
                "comparisons": {k: v.to_dict() for k, v in comparisons.items()},
                "overall_pass": all(r.is_acceptable for r in comparisons.values()),
            })

        return results
