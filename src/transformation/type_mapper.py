"""
Type Mapper for RPT to RDF Converter.

Maps Crystal Reports data types to Oracle data types.
"""

from dataclasses import dataclass
from typing import Optional

from ..parsing.report_model import DataType


@dataclass
class OracleType:
    """Oracle data type specification."""
    name: str
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None

    def __str__(self) -> str:
        """Return the Oracle type declaration."""
        if self.length:
            return f"{self.name}({self.length})"
        elif self.precision is not None:
            if self.scale is not None:
                return f"{self.name}({self.precision},{self.scale})"
            return f"{self.name}({self.precision})"
        return self.name


class TypeMapper:
    """Maps Crystal Reports data types to Oracle types."""

    # Default type mappings
    DEFAULT_MAPPINGS = {
        DataType.STRING: OracleType("VARCHAR2", length=4000),
        DataType.NUMBER: OracleType("NUMBER"),
        DataType.CURRENCY: OracleType("NUMBER", precision=15, scale=2),
        DataType.DATE: OracleType("DATE"),
        DataType.TIME: OracleType("DATE"),  # Oracle stores time in DATE
        DataType.DATETIME: OracleType("TIMESTAMP"),
        DataType.BOOLEAN: OracleType("VARCHAR2", length=1),  # 'Y'/'N'
        DataType.MEMO: OracleType("CLOB"),
        DataType.BLOB: OracleType("BLOB"),
        DataType.UNKNOWN: OracleType("VARCHAR2", length=4000),
    }

    # Crystal format to Oracle format string mappings
    FORMAT_MAPPINGS = {
        # Number formats
        "#,##0": "999,999,999,990",
        "#,##0.00": "999,999,999,990.00",
        "0.00": "990.00",
        "0": "990",
        "#,##0.00;(#,##0.00)": "999,999,999,990.00PR",  # Negative in parentheses
        "0%": "990%",
        "0.00%": "990.00%",

        # Currency formats
        "$#,##0": "$999,999,999,990",
        "$#,##0.00": "$999,999,999,990.00",
        "$#,##0.00;($#,##0.00)": "$999,999,999,990.00PR",

        # Date formats
        "MM/dd/yyyy": "MM/DD/YYYY",
        "dd/MM/yyyy": "DD/MM/YYYY",
        "yyyy-MM-dd": "YYYY-MM-DD",
        "MMMM d, yyyy": "MONTH DD, YYYY",
        "MMM d, yyyy": "MON DD, YYYY",
        "M/d/yy": "MM/DD/YY",

        # Time formats
        "h:mm:ss tt": "HH:MI:SS AM",
        "HH:mm:ss": "HH24:MI:SS",
        "h:mm tt": "HH:MI AM",
        "HH:mm": "HH24:MI",

        # DateTime formats
        "MM/dd/yyyy h:mm:ss tt": "MM/DD/YYYY HH:MI:SS AM",
        "yyyy-MM-dd HH:mm:ss": "YYYY-MM-DD HH24:MI:SS",
    }

    def __init__(self, custom_mappings: Optional[dict] = None):
        """Initialize the type mapper.

        Args:
            custom_mappings: Optional custom type mappings to override defaults.
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)

    def map_type(
        self,
        crystal_type: DataType,
        length: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
    ) -> OracleType:
        """Map a Crystal data type to Oracle type.

        Args:
            crystal_type: The Crystal Reports data type.
            length: Optional length override.
            precision: Optional precision override.
            scale: Optional scale override.

        Returns:
            OracleType specification.
        """
        base_type = self.mappings.get(crystal_type, self.mappings[DataType.UNKNOWN])

        # Apply overrides if provided
        if length is not None or precision is not None or scale is not None:
            return OracleType(
                name=base_type.name,
                length=length if length is not None else base_type.length,
                precision=precision if precision is not None else base_type.precision,
                scale=scale if scale is not None else base_type.scale,
            )

        return base_type

    def map_type_string(
        self,
        crystal_type: DataType,
        length: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
    ) -> str:
        """Map a Crystal data type to Oracle type string.

        Args:
            crystal_type: The Crystal Reports data type.
            length: Optional length override.
            precision: Optional precision override.
            scale: Optional scale override.

        Returns:
            Oracle type declaration string.
        """
        return str(self.map_type(crystal_type, length, precision, scale))

    def map_format_string(self, crystal_format: str) -> Optional[str]:
        """Map a Crystal format string to Oracle format.

        Args:
            crystal_format: Crystal Reports format string.

        Returns:
            Oracle format string, or None if no mapping exists.
        """
        if not crystal_format:
            return None

        # Check for exact match
        if crystal_format in self.FORMAT_MAPPINGS:
            return self.FORMAT_MAPPINGS[crystal_format]

        # Try to convert common patterns
        oracle_format = crystal_format

        # Date component replacements
        date_replacements = [
            ("yyyy", "YYYY"),
            ("yy", "YY"),
            ("MMMM", "MONTH"),
            ("MMM", "MON"),
            ("MM", "MM"),
            ("dd", "DD"),
            ("d", "D"),
        ]

        # Time component replacements
        time_replacements = [
            ("HH", "HH24"),
            ("hh", "HH"),
            ("mm", "MI"),
            ("ss", "SS"),
            ("tt", "AM"),
        ]

        for crystal_part, oracle_part in date_replacements + time_replacements:
            oracle_format = oracle_format.replace(crystal_part, oracle_part)

        return oracle_format if oracle_format != crystal_format else None

    def get_default_value(
        self,
        crystal_type: DataType,
        default: Optional[str] = None,
    ) -> str:
        """Get Oracle-compatible default value.

        Args:
            crystal_type: The Crystal data type.
            default: Original default value.

        Returns:
            Oracle-compatible default value expression.
        """
        if default is None:
            return "NULL"

        if crystal_type == DataType.BOOLEAN:
            # Convert boolean to Y/N
            if default.lower() in ("true", "yes", "1"):
                return "'Y'"
            return "'N'"

        if crystal_type == DataType.STRING or crystal_type == DataType.MEMO:
            # Escape single quotes
            escaped = default.replace("'", "''")
            return f"'{escaped}'"

        if crystal_type in (DataType.DATE, DataType.DATETIME):
            # Assume ISO format or Oracle default
            return f"TO_DATE('{default}', 'YYYY-MM-DD')"

        if crystal_type == DataType.TIME:
            return f"TO_DATE('1970-01-01 {default}', 'YYYY-MM-DD HH24:MI:SS')"

        # Numbers can pass through
        if crystal_type in (DataType.NUMBER, DataType.CURRENCY):
            return default

        return f"'{default}'"

    def requires_conversion_function(self, crystal_type: DataType) -> Optional[str]:
        """Check if a type requires a conversion function.

        Args:
            crystal_type: The Crystal data type.

        Returns:
            Conversion function name, or None if not needed.
        """
        conversion_functions = {
            DataType.DATETIME: "TO_TIMESTAMP",
            DataType.DATE: "TO_DATE",
            DataType.TIME: "TO_DATE",
        }
        return conversion_functions.get(crystal_type)

    def get_plsql_type(self, crystal_type: DataType) -> str:
        """Get PL/SQL variable type for a Crystal type.

        Args:
            crystal_type: The Crystal data type.

        Returns:
            PL/SQL type declaration.
        """
        plsql_types = {
            DataType.STRING: "VARCHAR2(4000)",
            DataType.NUMBER: "NUMBER",
            DataType.CURRENCY: "NUMBER",
            DataType.DATE: "DATE",
            DataType.TIME: "DATE",
            DataType.DATETIME: "TIMESTAMP",
            DataType.BOOLEAN: "BOOLEAN",  # PL/SQL supports BOOLEAN
            DataType.MEMO: "CLOB",
            DataType.BLOB: "BLOB",
            DataType.UNKNOWN: "VARCHAR2(4000)",
        }
        return plsql_types.get(crystal_type, "VARCHAR2(4000)")
