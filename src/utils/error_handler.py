"""
Error handling and reporting for RPT to RDF Converter.

Provides error categorization, collection, and report generation
for tracking conversion issues and generating actionable reports.

Error Code Format: RPT-XXXX
- RPT-1xxx: Extraction errors
- RPT-2xxx: Parsing errors
- RPT-3xxx: Formula errors
- RPT-4xxx: Type errors
- RPT-5xxx: Layout errors
- RPT-6xxx: Connection errors
- RPT-7xxx: Subreport errors
- RPT-8xxx: Generation errors
- RPT-9xxx: General/Configuration errors
"""

import csv
import html
import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ErrorCode(Enum):
    """Standardized error codes for the converter.

    Format: RPT-XXXX where X is a digit.
    - 1xxx: Extraction errors
    - 2xxx: Parsing errors
    - 3xxx: Formula errors
    - 4xxx: Type errors
    - 5xxx: Layout errors
    - 6xxx: Connection errors
    - 7xxx: Subreport errors
    - 8xxx: Generation errors
    - 9xxx: General/Configuration errors
    """

    # Extraction errors (1xxx)
    EXTRACTION_FAILED = "RPT-1001"
    EXTRACTION_TIMEOUT = "RPT-1002"
    RPT_FILE_NOT_FOUND = "RPT-1003"
    RPT_FILE_CORRUPT = "RPT-1004"
    RPT_FILE_EMPTY = "RPT-1005"
    RPTTOXML_NOT_FOUND = "RPT-1006"
    CRYSTAL_SDK_ERROR = "RPT-1007"

    # Parsing errors (2xxx)
    XML_PARSE_ERROR = "RPT-2001"
    XML_INVALID_STRUCTURE = "RPT-2002"
    MISSING_ROOT_ELEMENT = "RPT-2003"
    MISSING_REQUIRED_ELEMENT = "RPT-2004"
    INVALID_ATTRIBUTE_VALUE = "RPT-2005"
    ENCODING_ERROR = "RPT-2006"

    # Formula errors (3xxx)
    FORMULA_SYNTAX_ERROR = "RPT-3001"
    FORMULA_FUNCTION_UNKNOWN = "RPT-3002"
    FORMULA_FIELD_NOT_FOUND = "RPT-3003"
    FORMULA_TYPE_MISMATCH = "RPT-3004"
    FORMULA_CIRCULAR_REF = "RPT-3005"
    FORMULA_UNSUPPORTED_FEATURE = "RPT-3006"
    FORMULA_CONVERSION_PARTIAL = "RPT-3007"

    # Type errors (4xxx)
    TYPE_UNMAPPED = "RPT-4001"
    TYPE_CONVERSION_FAILED = "RPT-4002"
    TYPE_PRECISION_LOSS = "RPT-4003"
    TYPE_OVERFLOW = "RPT-4004"

    # Layout errors (5xxx)
    LAYOUT_TOO_COMPLEX = "RPT-5001"
    LAYOUT_NESTED_TOO_DEEP = "RPT-5002"
    COORDINATE_OVERFLOW = "RPT-5003"
    SECTION_OVERLAP = "RPT-5004"
    FONT_NOT_FOUND = "RPT-5005"
    IMAGE_NOT_FOUND = "RPT-5006"

    # Connection errors (6xxx)
    CONNECTION_FAILED = "RPT-6001"
    CONNECTION_TYPE_UNSUPPORTED = "RPT-6002"
    CONNECTION_STRING_INVALID = "RPT-6003"
    DATABASE_NOT_FOUND = "RPT-6004"
    AUTHENTICATION_FAILED = "RPT-6005"

    # Subreport errors (7xxx)
    SUBREPORT_NOT_FOUND = "RPT-7001"
    SUBREPORT_NESTED_TOO_DEEP = "RPT-7002"
    SUBREPORT_CIRCULAR_REF = "RPT-7003"
    SUBREPORT_PARAM_MISMATCH = "RPT-7004"

    # Generation errors (8xxx)
    XML_GENERATION_FAILED = "RPT-8001"
    RDF_CONVERSION_FAILED = "RPT-8002"
    RWCONVERTER_ERROR = "RPT-8003"
    RWCONVERTER_TIMEOUT = "RPT-8004"
    RWCONVERTER_NOT_FOUND = "RPT-8005"
    OUTPUT_WRITE_FAILED = "RPT-8006"

    # General/Configuration errors (9xxx)
    CONFIGURATION_INVALID = "RPT-9001"
    CONFIGURATION_MISSING = "RPT-9002"
    PERMISSION_DENIED = "RPT-9003"
    DISK_FULL = "RPT-9004"
    MEMORY_ERROR = "RPT-9005"
    UNKNOWN_ERROR = "RPT-9999"


# Mapping from ErrorCode to user-friendly descriptions and suggested fixes
ERROR_DETAILS: dict[ErrorCode, dict[str, str]] = {
    # Extraction errors
    ErrorCode.EXTRACTION_FAILED: {
        "description": "Failed to extract report content from RPT file",
        "suggestion": "Ensure the RPT file is valid and not corrupted. Try opening it in Crystal Reports.",
    },
    ErrorCode.EXTRACTION_TIMEOUT: {
        "description": "Extraction process timed out",
        "suggestion": "Increase timeout in configuration or check for issues with the report file.",
    },
    ErrorCode.RPT_FILE_NOT_FOUND: {
        "description": "The specified RPT file was not found",
        "suggestion": "Verify the file path is correct and the file exists.",
    },
    ErrorCode.RPT_FILE_CORRUPT: {
        "description": "The RPT file appears to be corrupted",
        "suggestion": "Try opening the file in Crystal Reports to verify it's valid.",
    },
    ErrorCode.RPT_FILE_EMPTY: {
        "description": "The RPT file is empty",
        "suggestion": "Ensure you're pointing to the correct file.",
    },
    ErrorCode.RPTTOXML_NOT_FOUND: {
        "description": "RptToXml tool not found",
        "suggestion": "Ensure RptToXml is installed and the path is configured correctly.",
    },
    ErrorCode.CRYSTAL_SDK_ERROR: {
        "description": "Crystal Reports SDK error",
        "suggestion": "Ensure Crystal Reports runtime is installed correctly.",
    },
    # Parsing errors
    ErrorCode.XML_PARSE_ERROR: {
        "description": "Failed to parse XML content",
        "suggestion": "The extracted XML may be malformed. Check the extraction step.",
    },
    ErrorCode.XML_INVALID_STRUCTURE: {
        "description": "XML structure is invalid or unexpected",
        "suggestion": "The report may use an unsupported Crystal Reports version.",
    },
    ErrorCode.MISSING_ROOT_ELEMENT: {
        "description": "XML is missing the root element",
        "suggestion": "The extraction may have failed silently. Re-run extraction.",
    },
    ErrorCode.MISSING_REQUIRED_ELEMENT: {
        "description": "A required element is missing from the report",
        "suggestion": "The report may be incomplete or using unsupported features.",
    },
    # Formula errors
    ErrorCode.FORMULA_SYNTAX_ERROR: {
        "description": "Formula has a syntax error",
        "suggestion": "Check the formula syntax in Crystal Reports and fix any errors.",
    },
    ErrorCode.FORMULA_FUNCTION_UNKNOWN: {
        "description": "Formula uses an unknown or unsupported function",
        "suggestion": "The function may need manual conversion to PL/SQL equivalent.",
    },
    ErrorCode.FORMULA_FIELD_NOT_FOUND: {
        "description": "Formula references a field that doesn't exist",
        "suggestion": "Verify field names in the formula match the data source.",
    },
    ErrorCode.FORMULA_UNSUPPORTED_FEATURE: {
        "description": "Formula uses an unsupported Crystal Reports feature",
        "suggestion": "This feature requires manual conversion to Oracle Reports.",
    },
    ErrorCode.FORMULA_CONVERSION_PARTIAL: {
        "description": "Formula was partially converted with some manual work needed",
        "suggestion": "Review the generated PL/SQL and complete any placeholder sections.",
    },
    # Type errors
    ErrorCode.TYPE_UNMAPPED: {
        "description": "Data type has no Oracle equivalent mapping",
        "suggestion": "Add a custom type mapping in the configuration.",
    },
    ErrorCode.TYPE_CONVERSION_FAILED: {
        "description": "Failed to convert data type",
        "suggestion": "Check if the data type is supported and add a custom mapping if needed.",
    },
    ErrorCode.TYPE_PRECISION_LOSS: {
        "description": "Type conversion may result in precision loss",
        "suggestion": "Review the Oracle type and adjust precision as needed.",
    },
    # Layout errors
    ErrorCode.LAYOUT_TOO_COMPLEX: {
        "description": "Report layout is too complex for automatic conversion",
        "suggestion": "Simplify the layout or convert complex sections manually.",
    },
    ErrorCode.LAYOUT_NESTED_TOO_DEEP: {
        "description": "Layout nesting exceeds supported depth",
        "suggestion": "Reduce nesting depth or flatten the layout structure.",
    },
    ErrorCode.COORDINATE_OVERFLOW: {
        "description": "Field coordinates exceed Oracle Reports limits",
        "suggestion": "Adjust field positions to fit within Oracle Reports bounds.",
    },
    ErrorCode.FONT_NOT_FOUND: {
        "description": "Font used in report is not available",
        "suggestion": "Add a font mapping in the configuration or install the font.",
    },
    # Connection errors
    ErrorCode.CONNECTION_FAILED: {
        "description": "Failed to establish database connection",
        "suggestion": "Verify connection string and database availability.",
    },
    ErrorCode.CONNECTION_TYPE_UNSUPPORTED: {
        "description": "Database connection type is not supported",
        "suggestion": "Convert to a supported connection type (ODBC, JDBC, Native).",
    },
    # Subreport errors
    ErrorCode.SUBREPORT_NOT_FOUND: {
        "description": "Referenced subreport file not found",
        "suggestion": "Ensure all subreport files are in the same directory.",
    },
    ErrorCode.SUBREPORT_NESTED_TOO_DEEP: {
        "description": "Subreport nesting exceeds supported depth",
        "suggestion": "Reduce subreport nesting or inline subreport content.",
    },
    ErrorCode.SUBREPORT_CIRCULAR_REF: {
        "description": "Circular subreport reference detected",
        "suggestion": "Remove the circular reference in the report structure.",
    },
    # Generation errors
    ErrorCode.XML_GENERATION_FAILED: {
        "description": "Failed to generate Oracle Reports XML",
        "suggestion": "Check the transformation output for errors.",
    },
    ErrorCode.RDF_CONVERSION_FAILED: {
        "description": "Failed to convert XML to RDF format",
        "suggestion": "Verify rwconverter is working and the XML is valid.",
    },
    ErrorCode.RWCONVERTER_ERROR: {
        "description": "rwconverter reported an error",
        "suggestion": "Check the rwconverter output for specific error details.",
    },
    ErrorCode.RWCONVERTER_TIMEOUT: {
        "description": "rwconverter process timed out",
        "suggestion": "Increase timeout or check for issues with the Oracle installation.",
    },
    ErrorCode.RWCONVERTER_NOT_FOUND: {
        "description": "rwconverter utility not found",
        "suggestion": "Verify ORACLE_HOME is set correctly and rwconverter is installed.",
    },
    # Configuration errors
    ErrorCode.CONFIGURATION_INVALID: {
        "description": "Configuration file is invalid",
        "suggestion": "Check the configuration file syntax and required fields.",
    },
    ErrorCode.CONFIGURATION_MISSING: {
        "description": "Required configuration is missing",
        "suggestion": "Create a configuration file or set required environment variables.",
    },
    ErrorCode.UNKNOWN_ERROR: {
        "description": "An unexpected error occurred",
        "suggestion": "Check the logs for more details and report if this persists.",
    },
}


def get_error_details(code: ErrorCode) -> dict[str, str]:
    """Get description and suggestion for an error code.

    Args:
        code: The error code to look up.

    Returns:
        Dictionary with 'description' and 'suggestion' keys.
    """
    return ERROR_DETAILS.get(code, {
        "description": "Unknown error",
        "suggestion": "Check the logs for more details.",
    })


class ErrorCategory(Enum):
    """Categories of conversion errors (legacy, maps to ErrorCode)."""

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


# Mapping from ErrorCategory to ErrorCode for backward compatibility
CATEGORY_TO_CODE: dict[ErrorCategory, ErrorCode] = {
    ErrorCategory.EXTRACTION_FAILED: ErrorCode.EXTRACTION_FAILED,
    ErrorCategory.EXTRACTION_TIMEOUT: ErrorCode.EXTRACTION_TIMEOUT,
    ErrorCategory.RPT_CORRUPT: ErrorCode.RPT_FILE_CORRUPT,
    ErrorCategory.PARSE_ERROR: ErrorCode.XML_PARSE_ERROR,
    ErrorCategory.XML_INVALID: ErrorCode.XML_INVALID_STRUCTURE,
    ErrorCategory.MISSING_ELEMENT: ErrorCode.MISSING_REQUIRED_ELEMENT,
    ErrorCategory.FORMULA_UNSUPPORTED: ErrorCode.FORMULA_UNSUPPORTED_FEATURE,
    ErrorCategory.FORMULA_SYNTAX_ERROR: ErrorCode.FORMULA_SYNTAX_ERROR,
    ErrorCategory.FORMULA_FUNCTION_UNKNOWN: ErrorCode.FORMULA_FUNCTION_UNKNOWN,
    ErrorCategory.TYPE_UNMAPPED: ErrorCode.TYPE_UNMAPPED,
    ErrorCategory.TYPE_CONVERSION_ERROR: ErrorCode.TYPE_CONVERSION_FAILED,
    ErrorCategory.LAYOUT_COMPLEX: ErrorCode.LAYOUT_TOO_COMPLEX,
    ErrorCategory.LAYOUT_NESTED_TOO_DEEP: ErrorCode.LAYOUT_NESTED_TOO_DEEP,
    ErrorCategory.COORDINATE_OVERFLOW: ErrorCode.COORDINATE_OVERFLOW,
    ErrorCategory.CONNECTION_ERROR: ErrorCode.CONNECTION_FAILED,
    ErrorCategory.CONNECTION_TYPE_UNSUPPORTED: ErrorCode.CONNECTION_TYPE_UNSUPPORTED,
    ErrorCategory.SUBREPORT_NESTED: ErrorCode.SUBREPORT_NESTED_TOO_DEEP,
    ErrorCategory.SUBREPORT_NOT_FOUND: ErrorCode.SUBREPORT_NOT_FOUND,
    ErrorCategory.SUBREPORT_CIRCULAR: ErrorCode.SUBREPORT_CIRCULAR_REF,
    ErrorCategory.XML_GENERATION_ERROR: ErrorCode.XML_GENERATION_FAILED,
    ErrorCategory.TEMPLATE_ERROR: ErrorCode.XML_GENERATION_FAILED,
    ErrorCategory.RDF_CONVERSION_FAILED: ErrorCode.RDF_CONVERSION_FAILED,
    ErrorCategory.RWCONVERTER_ERROR: ErrorCode.RWCONVERTER_ERROR,
    ErrorCategory.RWCONVERTER_TIMEOUT: ErrorCode.RWCONVERTER_TIMEOUT,
    ErrorCategory.UNKNOWN_ERROR: ErrorCode.UNKNOWN_ERROR,
    ErrorCategory.CONFIGURATION_ERROR: ErrorCode.CONFIGURATION_INVALID,
}


@dataclass
class ConversionError:
    """Represents a single conversion error or warning.

    Attributes:
        category: Legacy error category (use error_code for new code).
        message: Human-readable error message.
        error_code: Standardized error code (RPT-XXXX format).
        element_type: Type of element that caused the error (formula, field, etc.).
        element_name: Name of the element that caused the error.
        original_value: Original value that triggered the error.
        suggested_fix: Suggested action to resolve the error.
        is_fatal: Whether this error should halt processing.
        timestamp: When the error occurred.
        context: Additional context information.
    """

    category: ErrorCategory
    message: str
    error_code: Optional[ErrorCode] = None
    element_type: Optional[str] = None  # formula, field, section, etc.
    element_name: Optional[str] = None
    original_value: Optional[str] = None
    suggested_fix: Optional[str] = None
    is_fatal: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set error_code from category if not provided."""
        if self.error_code is None and self.category in CATEGORY_TO_CODE:
            self.error_code = CATEGORY_TO_CODE[self.category]

        # Auto-populate suggested_fix from error details if not provided
        if self.suggested_fix is None and self.error_code:
            details = get_error_details(self.error_code)
            self.suggested_fix = details.get("suggestion")

    @property
    def code(self) -> str:
        """Get the error code string (e.g., 'RPT-1001')."""
        if self.error_code:
            return self.error_code.value
        return "RPT-9999"

    @property
    def description(self) -> str:
        """Get the error description from error details."""
        if self.error_code:
            details = get_error_details(self.error_code)
            return details.get("description", self.message)
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "category": self.category.value,
            "message": self.message,
            "description": self.description,
            "element_type": self.element_type,
            "element_name": self.element_name,
            "original_value": self.original_value,
            "suggested_fix": self.suggested_fix,
            "is_fatal": self.is_fatal,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }

    def format_message(self, verbose: bool = False) -> str:
        """Format the error message for display.

        Args:
            verbose: If True, include additional details.

        Returns:
            Formatted error message string.
        """
        parts = [f"[{self.code}]", self.message]

        if self.element_name:
            parts.insert(1, f"({self.element_type}: {self.element_name})")

        if verbose and self.suggested_fix:
            parts.append(f"\n  Suggestion: {self.suggested_fix}")

        return " ".join(parts)


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
