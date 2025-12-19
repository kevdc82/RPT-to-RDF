"""
Parameter Mapper for RPT to RDF Converter.

Maps Crystal Reports parameters to Oracle Reports parameters.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ..parsing.report_model import Parameter, DataType
from .type_mapper import TypeMapper


@dataclass
class OracleParameter:
    """Oracle Reports parameter definition."""

    name: str
    oracle_name: str
    data_type: str
    width: int = 30
    initial_value: Optional[str] = None
    validation_trigger: Optional[str] = None
    list_of_values: Optional[str] = None  # SQL for LOV
    input_mask: Optional[str] = None
    prompt_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "oracle_name": self.oracle_name,
            "data_type": self.data_type,
            "width": self.width,
            "initial_value": self.initial_value,
            "validation_trigger": self.validation_trigger,
            "list_of_values": self.list_of_values,
            "input_mask": self.input_mask,
            "prompt_text": self.prompt_text,
        }


class ParameterMapper:
    """Maps Crystal Reports parameters to Oracle Reports parameters."""

    def __init__(self, parameter_prefix: str = "P_"):
        """Initialize the parameter mapper.

        Args:
            parameter_prefix: Prefix for Oracle parameter names.
        """
        self.parameter_prefix = parameter_prefix
        self.type_mapper = TypeMapper()

    def map_parameter(self, param: Parameter) -> OracleParameter:
        """Map a Crystal parameter to Oracle parameter.

        Args:
            param: Crystal Reports parameter.

        Returns:
            Oracle parameter definition.
        """
        # Create Oracle parameter name
        oracle_name = self._make_oracle_name(param.name)

        # Map data type
        oracle_type = self.type_mapper.map_type_string(param.data_type)

        # Calculate width
        width = self._calculate_width(param.data_type)

        # Map initial value
        initial_value = None
        if param.default_value is not None:
            initial_value = self.type_mapper.get_default_value(
                param.data_type, str(param.default_value)
            )

        # Create LOV SQL if list of values provided
        lov_sql = None
        if param.list_of_values:
            lov_sql = self._create_lov_sql(param.list_of_values)

        return OracleParameter(
            name=param.name,
            oracle_name=oracle_name,
            data_type=oracle_type,
            width=width,
            initial_value=initial_value,
            list_of_values=lov_sql,
            prompt_text=param.prompt_text or param.name,
        )

    def _make_oracle_name(self, name: str) -> str:
        """Create Oracle-compatible parameter name."""
        # Remove ? prefix if present
        if name.startswith("?"):
            name = name[1:]

        # Replace invalid characters
        import re
        oracle_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure starts with letter
        if oracle_name and oracle_name[0].isdigit():
            oracle_name = "P" + oracle_name

        # Add prefix
        if not oracle_name.upper().startswith(self.parameter_prefix.upper()):
            oracle_name = self.parameter_prefix + oracle_name

        return oracle_name.upper()

    def _calculate_width(self, data_type: DataType) -> int:
        """Calculate display width for parameter."""
        width_map = {
            DataType.STRING: 30,
            DataType.NUMBER: 15,
            DataType.CURRENCY: 15,
            DataType.DATE: 12,
            DataType.TIME: 10,
            DataType.DATETIME: 22,
            DataType.BOOLEAN: 5,
            DataType.MEMO: 60,
        }
        return width_map.get(data_type, 30)

    def _create_lov_sql(self, values: list) -> str:
        """Create SQL for list of values."""
        if not values:
            return None

        # Create UNION ALL query for static values
        parts = []
        for value in values:
            escaped = str(value).replace("'", "''")
            parts.append(f"SELECT '{escaped}' AS value FROM DUAL")

        return " UNION ALL ".join(parts)

    def batch_map(self, parameters: list[Parameter]) -> list[OracleParameter]:
        """Map multiple parameters.

        Args:
            parameters: List of Crystal parameters.

        Returns:
            List of Oracle parameters.
        """
        return [self.map_parameter(p) for p in parameters]
