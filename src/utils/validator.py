"""
Validation utilities for RPT to RDF Converter.

Provides validation functions for checking report structure,
XML validity, and conversion results.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .error_handler import ConversionError, ErrorCategory


class ReportValidator:
    """Validates report files and conversion results."""

    # Required Oracle Reports XML elements
    REQUIRED_ELEMENTS = ["report", "data"]
    RECOMMENDED_ELEMENTS = ["layout", "programUnits"]

    def __init__(self):
        """Initialize validator."""
        self.errors: list[ConversionError] = []
        self.warnings: list[ConversionError] = []

    def clear(self) -> None:
        """Clear validation results."""
        self.errors.clear()
        self.warnings.clear()

    def validate_rpt_file(self, rpt_path: Path) -> bool:
        """Validate an RPT file exists and is readable.

        Args:
            rpt_path: Path to RPT file.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        if not rpt_path.exists():
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"RPT file does not exist: {rpt_path}",
                    is_fatal=True,
                )
            )
            return False

        if not rpt_path.is_file():
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.EXTRACTION_FAILED,
                    message=f"Path is not a file: {rpt_path}",
                    is_fatal=True,
                )
            )
            return False

        # Check file size (empty files are invalid)
        if rpt_path.stat().st_size == 0:
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.RPT_CORRUPT,
                    message=f"RPT file is empty: {rpt_path}",
                    is_fatal=True,
                )
            )
            return False

        # Check file extension
        if rpt_path.suffix.lower() != ".rpt":
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.UNKNOWN_ERROR,
                    message=f"File does not have .rpt extension: {rpt_path}",
                )
            )

        return True

    def validate_crystal_xml(self, xml_path: Path) -> bool:
        """Validate extracted Crystal Reports XML.

        Args:
            xml_path: Path to extracted XML file.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        if not xml_path.exists():
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.PARSE_ERROR,
                    message=f"XML file does not exist: {xml_path}",
                    is_fatal=True,
                )
            )
            return False

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.XML_INVALID,
                    message=f"Invalid XML: {e}",
                    is_fatal=True,
                )
            )
            return False

        # Check for expected Crystal Reports XML structure
        # RptToXml typically produces XML with a specific structure
        if root.tag not in ["CrystalReport", "Report", "report"]:
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.PARSE_ERROR,
                    message=f"Unexpected root element: {root.tag}",
                )
            )

        return len(self.errors) == 0

    def validate_oracle_xml(self, xml_content: str) -> bool:
        """Validate generated Oracle Reports XML.

        Args:
            xml_content: Oracle Reports XML content.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.XML_GENERATION_ERROR,
                    message=f"Generated XML is invalid: {e}",
                    is_fatal=True,
                )
            )
            return False

        # Check for required elements
        for element in self.REQUIRED_ELEMENTS:
            if element == "report":
                if root.tag != "report":
                    self.errors.append(
                        ConversionError(
                            category=ErrorCategory.XML_GENERATION_ERROR,
                            message=f"Root element must be 'report', got '{root.tag}'",
                            is_fatal=True,
                        )
                    )
            elif root.find(element) is None:
                self.errors.append(
                    ConversionError(
                        category=ErrorCategory.MISSING_ELEMENT,
                        message=f"Missing required element: {element}",
                        is_fatal=True,
                    )
                )

        # Check for recommended elements
        for element in self.RECOMMENDED_ELEMENTS:
            if root.find(element) is None:
                self.warnings.append(
                    ConversionError(
                        category=ErrorCategory.MISSING_ELEMENT,
                        message=f"Missing recommended element: {element}",
                    )
                )

        # Validate DTD version
        dtd_version = root.get("DTDVersion")
        if not dtd_version:
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.XML_GENERATION_ERROR,
                    message="Missing DTDVersion attribute on report element",
                )
            )

        return len(self.errors) == 0

    def validate_rdf_file(self, rdf_path: Path) -> bool:
        """Validate generated RDF file.

        Args:
            rdf_path: Path to RDF file.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        if not rdf_path.exists():
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"RDF file was not created: {rdf_path}",
                    is_fatal=True,
                )
            )
            return False

        # Check file size (very small files might be corrupt)
        if rdf_path.stat().st_size < 100:
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.RDF_CONVERSION_FAILED,
                    message=f"RDF file is too small, possibly corrupt: {rdf_path}",
                    is_fatal=True,
                )
            )
            return False

        return True

    def validate_data_source(
        self,
        connection_type: str,
        connection_string: Optional[str],
    ) -> bool:
        """Validate a data source configuration.

        Args:
            connection_type: Type of database connection.
            connection_string: Connection string.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        supported_types = ["ODBC", "OLE DB", "JDBC", "Native", "Oracle"]

        if not connection_type:
            self.errors.append(
                ConversionError(
                    category=ErrorCategory.CONNECTION_ERROR,
                    message="Connection type is empty",
                    is_fatal=True,
                )
            )
            return False

        if connection_type not in supported_types:
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.CONNECTION_TYPE_UNSUPPORTED,
                    message=f"Connection type '{connection_type}' may not be supported",
                    suggested_fix=f"Consider using one of: {', '.join(supported_types)}",
                )
            )

        if not connection_string:
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.CONNECTION_ERROR,
                    message="Connection string is empty",
                )
            )

        return len(self.errors) == 0

    def validate_formula(self, formula_text: str, formula_name: str) -> bool:
        """Validate a Crystal Reports formula.

        Args:
            formula_text: Formula expression text.
            formula_name: Name of the formula.

        Returns:
            True if valid, False otherwise.
        """
        self.clear()

        if not formula_text or not formula_text.strip():
            self.warnings.append(
                ConversionError(
                    category=ErrorCategory.FORMULA_UNSUPPORTED,
                    message=f"Formula '{formula_name}' is empty",
                )
            )
            return True  # Empty formulas are technically valid

        # Check for obviously problematic patterns
        problematic_patterns = [
            ("WhilePrintingRecords", "May require special handling for print-time evaluation"),
            ("WhileReadingRecords", "May require special handling for read-time evaluation"),
            ("EvaluateAfter", "Evaluation order may need manual adjustment"),
            ("SharedVariable", "Shared variables need conversion to package variables"),
        ]

        for pattern, suggestion in problematic_patterns:
            if pattern.lower() in formula_text.lower():
                self.warnings.append(
                    ConversionError(
                        category=ErrorCategory.FORMULA_UNSUPPORTED,
                        message=f"Formula '{formula_name}' contains '{pattern}'",
                        element_type="formula",
                        element_name=formula_name,
                        original_value=formula_text[:100],
                        suggested_fix=suggestion,
                    )
                )

        return len(self.errors) == 0

    def get_validation_summary(self) -> dict:
        """Get summary of validation results.

        Returns:
            Dictionary with validation summary.
        """
        return {
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }
