"""
Condition Mapper for RPT to RDF Converter.

Converts Crystal Reports suppress conditions and conditional formatting
to Oracle Reports format triggers.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from ..parsing.report_model import FontSpec, FormatSpec
from ..utils.logger import get_logger


@dataclass
class FormatTrigger:
    """Oracle Reports format trigger definition."""

    name: str
    plsql_code: str
    trigger_type: str = "suppress"  # suppress, conditional_format
    original_condition: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "plsql_code": self.plsql_code,
            "trigger_type": self.trigger_type,
            "original_condition": self.original_condition,
            "warnings": self.warnings,
        }


class ConditionMapper:
    """Converts Crystal Reports conditions to Oracle Reports format triggers."""

    # Crystal operators to PL/SQL operators
    OPERATOR_MAP = {
        "=": "=",
        "<>": "!=",
        "!=": "!=",
        ">": ">",
        "<": "<",
        ">=": ">=",
        "<=": "<=",
        "and": "AND",
        "or": "OR",
        "not": "NOT",
        "is null": "IS NULL",
        "is not null": "IS NOT NULL",
    }

    # Crystal functions that map to PL/SQL functions
    FUNCTION_MAP = {
        "isnull": "({0} IS NULL)",
        "isnotnull": "({0} IS NOT NULL)",
        "trim": "TRIM({0})",
        "upper": "UPPER({0})",
        "lower": "LOWER({0})",
        "len": "LENGTH({0})",
        "length": "LENGTH({0})",
    }

    def __init__(self, trigger_prefix: str = "FT_"):
        """Initialize the condition mapper.

        Args:
            trigger_prefix: Prefix for format trigger function names.
        """
        self.trigger_prefix = trigger_prefix
        self.logger = get_logger("condition_mapper")
        self._trigger_counter = 0

    def convert_suppress_condition(
        self,
        crystal_condition: str,
        field_name: str = "",
    ) -> FormatTrigger:
        """Convert Crystal suppress condition to Oracle format trigger.

        Args:
            crystal_condition: Crystal formula for suppressing the field/section.
            field_name: Name of the field (used for trigger naming).

        Returns:
            FormatTrigger with PL/SQL function that returns TRUE to suppress.
        """
        self._trigger_counter += 1
        trigger_name = f"{self.trigger_prefix}SUPPRESS_{self._trigger_counter}"
        if field_name:
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", field_name.upper())
            trigger_name = f"{self.trigger_prefix}SUPPRESS_{safe_name}"

        warnings = []
        plsql_condition = self._convert_condition_expression(crystal_condition, warnings)

        # Generate PL/SQL function
        plsql_code = f"""function {trigger_name} return boolean is
begin
  return {plsql_condition};
exception
  when others then
    return FALSE;
end;"""

        return FormatTrigger(
            name=trigger_name,
            plsql_code=plsql_code,
            trigger_type="suppress",
            original_condition=crystal_condition,
            warnings=warnings,
        )

    def convert_conditional_format(
        self,
        condition: str,
        format_spec: dict,
        field_name: str = "",
    ) -> FormatTrigger:
        """Convert conditional formatting to Oracle format trigger.

        Args:
            condition: Crystal formula for the condition.
            format_spec: Dictionary with format properties (color, font, etc.).
            field_name: Name of the field.

        Returns:
            FormatTrigger with PL/SQL function for conditional formatting.

        Note:
            Oracle Reports format triggers primarily control visibility.
            Color/font changes may require post-processing or custom properties.
        """
        self._trigger_counter += 1
        trigger_name = f"{self.trigger_prefix}FORMAT_{self._trigger_counter}"
        if field_name:
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", field_name.upper())
            trigger_name = f"{self.trigger_prefix}FORMAT_{safe_name}"

        warnings = []
        plsql_condition = self._convert_condition_expression(condition, warnings)

        # Note: Oracle Reports format triggers are limited compared to Crystal
        # They mainly control visibility, not font/color changes
        warnings.append(
            "Oracle Reports format triggers have limited formatting capabilities. "
            "Font/color changes may require manual implementation."
        )

        plsql_code = f"""function {trigger_name} return boolean is
begin
  -- Conditional formatting: {format_spec}
  return {plsql_condition};
exception
  when others then
    return FALSE;
end;"""

        return FormatTrigger(
            name=trigger_name,
            plsql_code=plsql_code,
            trigger_type="conditional_format",
            original_condition=condition,
            warnings=warnings,
        )

    def _convert_condition_expression(
        self,
        crystal_expr: str,
        warnings: list[str],
    ) -> str:
        """Convert a Crystal condition expression to PL/SQL.

        Args:
            crystal_expr: Crystal Reports condition expression.
            warnings: List to accumulate warnings.

        Returns:
            PL/SQL boolean expression.
        """
        if not crystal_expr or not crystal_expr.strip():
            return "FALSE"

        expr = crystal_expr.strip()

        # Remove Crystal formula delimiters if the entire expression is wrapped
        # Only strip if it's a single balanced brace pair (no other braces inside)
        if expr.startswith("{") and expr.endswith("}"):
            # Check if there are other braces inside - if so, these are field references
            inner = expr[1:-1]
            if "{" not in inner and "}" not in inner:
                expr = inner.strip()

        # Convert field references from {table.field} to :FIELD
        expr = self._convert_field_references(expr)

        # Convert Crystal operators to PL/SQL
        expr = self._convert_operators(expr)

        # Convert Crystal functions to PL/SQL
        expr = self._convert_functions(expr, warnings)

        # Handle special cases
        expr = self._handle_special_cases(expr, warnings)

        return expr

    def _convert_field_references(self, expr: str) -> str:
        """Convert Crystal field references to Oracle bind variable references.

        Crystal: {table.field} or {field}
        Oracle: :FIELD
        """
        # Match {table.field} or {field} - capture the field name after optional table prefix
        pattern = r"\{([^}]+)\}"

        def replace_field(match):
            field_content = match.group(1)
            # If there's a table prefix (e.g., "orders.amount"), extract just the field
            if "." in field_content:
                field_name = field_content.split(".")[-1]
            else:
                field_name = field_content
            return f":{field_name.upper()}"

        return re.sub(pattern, replace_field, expr)

    def _convert_operators(self, expr: str) -> str:
        """Convert Crystal operators to PL/SQL operators."""
        result = expr

        # Sort by length (longest first) to handle multi-character operators
        operators = sorted(self.OPERATOR_MAP.items(), key=lambda x: -len(x[0]))

        for crystal_op, plsql_op in operators:
            # Use word boundaries for word operators like "and", "or", "not"
            if crystal_op.isalpha():
                # Case-insensitive replacement with word boundaries
                pattern = r"\b" + re.escape(crystal_op) + r"\b"
                result = re.sub(pattern, plsql_op, result, flags=re.IGNORECASE)
            else:
                # Direct replacement for symbols
                result = result.replace(crystal_op, plsql_op)

        return result

    def _convert_functions(self, expr: str, warnings: list[str]) -> str:
        """Convert Crystal functions to PL/SQL functions."""
        result = expr

        for crystal_func, plsql_template in self.FUNCTION_MAP.items():
            # Match function calls: FunctionName(args)
            pattern = r"\b" + re.escape(crystal_func) + r"\s*\(([^)]+)\)"

            def replace_func(match):
                args = match.group(1).strip()
                try:
                    return plsql_template.format(args)
                except (IndexError, KeyError):
                    warnings.append(f"Could not convert function {crystal_func}({args})")
                    return match.group(0)

            result = re.sub(pattern, replace_func, result, flags=re.IGNORECASE)

        return result

    def _handle_special_cases(self, expr: str, warnings: list[str]) -> str:
        """Handle special Crystal expression patterns."""
        # Handle boolean literals
        expr = re.sub(r"\btrue\b", "TRUE", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bfalse\b", "FALSE", expr, flags=re.IGNORECASE)

        # Handle string concatenation: Crystal uses & or +, PL/SQL uses ||
        expr = re.sub(r"(\S)\s*&\s*(\S)", r"\1 || \2", expr)

        # Handle null checks
        expr = re.sub(r"\b(\w+)\s*=\s*null\b", r"\1 IS NULL", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\b(\w+)\s*!=\s*null\b", r"\1 IS NOT NULL", expr, flags=re.IGNORECASE)

        return expr

    def generate_format_trigger_program_unit(self, trigger: FormatTrigger) -> str:
        """Generate complete PL/SQL program unit for a format trigger.

        Args:
            trigger: FormatTrigger object.

        Returns:
            Complete PL/SQL function definition.
        """
        return trigger.plsql_code

    def convert_suppress_if_conditions(
        self, format_spec: FormatSpec, field_name: str = ""
    ) -> Optional[FormatTrigger]:
        """Convert suppress_if_zero/suppress_if_blank to format trigger.

        Args:
            format_spec: FormatSpec from the field.
            field_name: Name of the field.

        Returns:
            FormatTrigger if suppress conditions exist, None otherwise.
        """
        conditions = []

        if format_spec.suppress_if_zero:
            conditions.append(f":{field_name.upper()} = 0")

        if format_spec.suppress_if_blank:
            conditions.append(
                f"(:{field_name.upper()} IS NULL OR TRIM(TO_CHAR(:{field_name.upper()})) = '')"
            )

        if not conditions:
            return None

        # Combine with OR
        combined_condition = " OR ".join(conditions)

        self._trigger_counter += 1
        trigger_name = f"{self.trigger_prefix}SUPPRESS_COND_{self._trigger_counter}"
        if field_name:
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", field_name.upper())
            trigger_name = f"{self.trigger_prefix}SUPPRESS_COND_{safe_name}"

        plsql_code = f"""function {trigger_name} return boolean is
begin
  return {combined_condition};
exception
  when others then
    return FALSE;
end;"""

        return FormatTrigger(
            name=trigger_name,
            plsql_code=plsql_code,
            trigger_type="suppress",
            original_condition=f"suppress_if_zero={format_spec.suppress_if_zero}, suppress_if_blank={format_spec.suppress_if_blank}",
            warnings=[],
        )

    def reset_counter(self) -> None:
        """Reset the trigger counter (useful for testing)."""
        self._trigger_counter = 0
