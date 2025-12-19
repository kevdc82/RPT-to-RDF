"""
Error handling and reporting for RPT to RDF Converter.

Provides error categorization, collection, and report generation
for tracking conversion issues and generating actionable reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import html
import csv
import json


class ErrorCategory(Enum):
    """Categories of conversion errors."""

    # Extraction errors
    EXTRACTION_FAILED = "extraction_failed"
    EXTRACTION_TIMEOUT = "extraction_timeout"
    RPT_CORRUPT = "rpt_corrupt"

    # Parsing errors
    PARSE_ERROR = "parse_error"
    XML_INVALID = "xml_invalid"
    MISSING_ELEMENT = "missing_element"

    # Formula errors
    FORMULA_UNSUPPORTED = "formula_unsupported"
    FORMULA_SYNTAX_ERROR = "formula_syntax_error"
    FORMULA_FUNCTION_UNKNOWN = "formula_function_unknown"

    # Type errors
    TYPE_UNMAPPED = "type_unmapped"
    TYPE_CONVERSION_ERROR = "type_conversion_error"

    # Layout errors
    LAYOUT_COMPLEX = "layout_complex"
    LAYOUT_NESTED_TOO_DEEP = "layout_nested_too_deep"
    COORDINATE_OVERFLOW = "coordinate_overflow"

    # Connection errors
    CONNECTION_ERROR = "connection_error"
    CONNECTION_TYPE_UNSUPPORTED = "connection_type_unsupported"

    # Subreport errors
    SUBREPORT_NESTED = "subreport_nested"
    SUBREPORT_NOT_FOUND = "subreport_not_found"
    SUBREPORT_CIRCULAR = "subreport_circular"

    # Generation errors
    XML_GENERATION_ERROR = "xml_generation_error"
    TEMPLATE_ERROR = "template_error"

    # RDF conversion errors
    RDF_CONVERSION_FAILED = "rdf_conversion"
    RWCONVERTER_ERROR = "rwconverter_error"
    RWCONVERTER_TIMEOUT = "rwconverter_timeout"

    # General errors
    UNKNOWN_ERROR = "unknown_error"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass
class ConversionError:
    """Represents a single conversion error or warning."""

    category: ErrorCategory
    message: str
    element_type: Optional[str] = None  # formula, field, section, etc.
    element_name: Optional[str] = None
    original_value: Optional[str] = None
    suggested_fix: Optional[str] = None
    is_fatal: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "message": self.message,
            "element_type": self.element_type,
            "element_name": self.element_name,
            "original_value": self.original_value,
            "suggested_fix": self.suggested_fix,
            "is_fatal": self.is_fatal,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


@dataclass
class PartialConversion:
    """Represents a partial conversion result (with warnings)."""

    file_name: str
    rdf_path: str
    warnings: list[ConversionError] = field(default_factory=list)
    elements_converted: int = 0
    elements_with_issues: int = 0
    completion_percentage: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_name": self.file_name,
            "rdf_path": self.rdf_path,
            "warnings": [w.to_dict() for w in self.warnings],
            "elements_converted": self.elements_converted,
            "elements_with_issues": self.elements_with_issues,
            "completion_percentage": self.completion_percentage,
        }


@dataclass
class FailedConversion:
    """Represents a failed conversion."""

    file_name: str
    errors: list[ConversionError] = field(default_factory=list)
    stage_failed: str = "unknown"  # extraction, parsing, transformation, generation, rdf_conversion
    partial_output: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_name": self.file_name,
            "errors": [e.to_dict() for e in self.errors],
            "stage_failed": self.stage_failed,
            "partial_output": self.partial_output,
        }


@dataclass
class ConversionReport:
    """Complete report of a batch conversion run."""

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_files: int = 0
    successful: int = 0
    partial: int = 0
    failed: int = 0

    successful_files: list[str] = field(default_factory=list)
    partial_files: list[PartialConversion] = field(default_factory=list)
    failed_files: list[FailedConversion] = field(default_factory=list)

    configuration: dict[str, Any] = field(default_factory=dict)

    def finalize(self) -> None:
        """Mark the conversion as complete."""
        self.end_time = datetime.now()

    @property
    def duration(self) -> Optional[float]:
        """Get duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "total_files": self.total_files,
            "successful": self.successful,
            "partial": self.partial,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "successful_files": self.successful_files,
            "partial_files": [p.to_dict() for p in self.partial_files],
            "failed_files": [f.to_dict() for f in self.failed_files],
            "configuration": self.configuration,
        }

    def generate_html_report(self) -> str:
        """Generate HTML report for review."""
        duration_str = f"{self.duration:.2f}s" if self.duration else "N/A"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPT to RDF Conversion Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.success {{ background: #d4edda; color: #155724; }}
        .stat-card.partial {{ background: #fff3cd; color: #856404; }}
        .stat-card.failed {{ background: #f8d7da; color: #721c24; }}
        .stat-card.info {{ background: #d1ecf1; color: #0c5460; }}
        .stat-value {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; text-transform: uppercase; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .error-category {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: #e9ecef;
        }}
        .error-category.formula {{ background: #ffeeba; }}
        .error-category.layout {{ background: #b8daff; }}
        .error-category.extraction {{ background: #f5c6cb; }}
        .suggested-fix {{
            background: #e8f5e9;
            padding: 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            margin-top: 5px;
        }}
        .collapsible {{
            cursor: pointer;
            padding: 10px;
            background: #f8f9fa;
            border: none;
            width: 100%;
            text-align: left;
            font-size: 16px;
        }}
        .collapsible:hover {{ background: #e9ecef; }}
        .content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
        }}
        .content.show {{ display: block; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RPT to RDF Conversion Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="stat-card info">
                <div class="stat-value">{self.total_files}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{self.successful}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card partial">
                <div class="stat-value">{self.partial}</div>
                <div class="stat-label">Partial</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value">{self.failed}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>

        <p><strong>Duration:</strong> {duration_str} |
           <strong>Success Rate:</strong> {self.success_rate:.1f}%</p>
"""

        # Successful files section
        if self.successful_files:
            html_content += """
        <h2>Successful Conversions</h2>
        <button class="collapsible">Show {count} successful files</button>
        <div class="content">
            <ul>
""".format(count=len(self.successful_files))
            for f in self.successful_files:
                html_content += f"                <li>{html.escape(f)}</li>\n"
            html_content += """            </ul>
        </div>
"""

        # Partial conversions section
        if self.partial_files:
            html_content += """
        <h2>Partial Conversions (Require Review)</h2>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Completion</th>
                    <th>Issues</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
            for p in self.partial_files:
                warnings_html = ""
                for w in p.warnings[:5]:  # Show first 5 warnings
                    cat_class = "formula" if "formula" in w.category.value else (
                        "layout" if "layout" in w.category.value else ""
                    )
                    warnings_html += f"""
                        <div>
                            <span class="error-category {cat_class}">{w.category.value}</span>
                            {html.escape(w.message)}
                        </div>"""
                    if w.suggested_fix:
                        warnings_html += f"""
                        <div class="suggested-fix">Fix: {html.escape(w.suggested_fix)}</div>"""

                if len(p.warnings) > 5:
                    warnings_html += f"<div>... and {len(p.warnings) - 5} more issues</div>"

                html_content += f"""
                <tr>
                    <td>{html.escape(p.file_name)}</td>
                    <td>{p.completion_percentage:.1f}%</td>
                    <td>{p.elements_with_issues}</td>
                    <td>{warnings_html}</td>
                </tr>
"""
            html_content += """            </tbody>
        </table>
"""

        # Failed conversions section
        if self.failed_files:
            html_content += """
        <h2>Failed Conversions</h2>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Stage Failed</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
"""
            for f in self.failed_files:
                errors_html = ""
                for e in f.errors:
                    errors_html += f"""
                        <div>
                            <span class="error-category extraction">{e.category.value}</span>
                            {html.escape(e.message)}
                        </div>"""
                    if e.suggested_fix:
                        errors_html += f"""
                        <div class="suggested-fix">Fix: {html.escape(e.suggested_fix)}</div>"""

                html_content += f"""
                <tr>
                    <td>{html.escape(f.file_name)}</td>
                    <td>{html.escape(f.stage_failed)}</td>
                    <td>{errors_html}</td>
                </tr>
"""
            html_content += """            </tbody>
        </table>
"""

        html_content += """
    </div>
    <script>
        document.querySelectorAll('.collapsible').forEach(btn => {
            btn.addEventListener('click', function() {
                this.nextElementSibling.classList.toggle('show');
            });
        });
    </script>
</body>
</html>
"""
        return html_content

    def generate_csv_summary(self) -> str:
        """Generate CSV summary for tracking."""
        output = []

        # Header
        output.append([
            "File Name",
            "Status",
            "Completion %",
            "Issues Count",
            "Stage Failed",
            "Primary Error",
        ])

        # Successful files
        for f in self.successful_files:
            output.append([f, "SUCCESS", "100", "0", "", ""])

        # Partial files
        for p in self.partial_files:
            primary_error = p.warnings[0].message if p.warnings else ""
            output.append([
                p.file_name,
                "PARTIAL",
                str(p.completion_percentage),
                str(p.elements_with_issues),
                "",
                primary_error,
            ])

        # Failed files
        for f in self.failed_files:
            primary_error = f.errors[0].message if f.errors else ""
            output.append([
                f.file_name,
                "FAILED",
                "0",
                str(len(f.errors)),
                f.stage_failed,
                primary_error,
            ])

        # Convert to CSV string
        import io
        string_io = io.StringIO()
        writer = csv.writer(string_io)
        writer.writerows(output)
        return string_io.getvalue()

    def save_reports(self, output_dir: str) -> tuple[str, str, str]:
        """Save all report formats to directory.

        Args:
            output_dir: Directory to save reports.

        Returns:
            Tuple of (html_path, csv_path, json_path).
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save HTML report
        html_path = output_path / f"conversion_report_{timestamp}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.generate_html_report())

        # Save CSV summary
        csv_path = output_path / f"conversion_summary_{timestamp}.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            f.write(self.generate_csv_summary())

        # Save JSON details
        json_path = output_path / f"conversion_details_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

        return str(html_path), str(csv_path), str(json_path)


class ErrorHandler:
    """Collects and manages errors during conversion."""

    def __init__(self):
        """Initialize error handler."""
        self.errors: list[ConversionError] = []
        self.warnings: list[ConversionError] = []

    def add_error(self, error: ConversionError) -> None:
        """Add an error to the collection.

        Args:
            error: The error to add.
        """
        if error.is_fatal:
            self.errors.append(error)
        else:
            self.warnings.append(error)

    def create_error(
        self,
        category: ErrorCategory,
        message: str,
        element_type: Optional[str] = None,
        element_name: Optional[str] = None,
        original_value: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        is_fatal: bool = False,
        **context,
    ) -> ConversionError:
        """Create and add an error.

        Args:
            category: Error category.
            message: Error message.
            element_type: Type of element that caused the error.
            element_name: Name of the element.
            original_value: Original value that caused the error.
            suggested_fix: Suggested fix for the error.
            is_fatal: Whether this error should stop conversion.
            **context: Additional context.

        Returns:
            The created error.
        """
        error = ConversionError(
            category=category,
            message=message,
            element_type=element_type,
            element_name=element_name,
            original_value=original_value,
            suggested_fix=suggested_fix,
            is_fatal=is_fatal,
            context=context,
        )
        self.add_error(error)
        return error

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        return len(self.errors) > 0

    def clear(self) -> None:
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()

    def get_summary(self) -> dict[str, int]:
        """Get summary of errors by category."""
        summary: dict[str, int] = {}

        for error in self.errors + self.warnings:
            key = error.category.value
            summary[key] = summary.get(key, 0) + 1

        return summary
