"""
Formula Translator for RPT to RDF Converter.

Translates Crystal Reports formulas to Oracle PL/SQL.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..parsing.report_model import Formula, DataType, FormulaSyntax
from ..utils.error_handler import ErrorHandler, ErrorCategory, ConversionError
from ..utils.logger import get_logger


@dataclass
class TranslatedFormula:
    """Result of translating a Crystal formula to PL/SQL."""

    original_name: str
    oracle_name: str
    plsql_code: str
    return_type: str
    success: bool = True
    is_placeholder: bool = False
    warnings: list[str] = field(default_factory=list)
    referenced_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_name": self.original_name,
            "oracle_name": self.oracle_name,
            "plsql_code": self.plsql_code,
            "return_type": self.return_type,
            "success": self.success,
            "is_placeholder": self.is_placeholder,
            "warnings": self.warnings,
            "referenced_columns": self.referenced_columns,
        }


class FormulaTranslator:
    """Translates Crystal Reports formulas to Oracle PL/SQL."""

    # Crystal function to PL/SQL function mapping
    # Format: 'CrystalFunction': ('oracle_template', num_args)
    FUNCTION_MAP = {
        # String functions
        "left": ("SUBSTR({0}, 1, {1})", 2),
        "right": ("SUBSTR({0}, -1 * {1})", 2),
        "mid": ("SUBSTR({0}, {1}, {2})", 3),
        "trim": ("TRIM({0})", 1),
        "ltrim": ("LTRIM({0})", 1),
        "rtrim": ("RTRIM({0})", 1),
        "upper": ("UPPER({0})", 1),
        "ucase": ("UPPER({0})", 1),
        "lower": ("LOWER({0})", 1),
        "lcase": ("LOWER({0})", 1),
        "length": ("LENGTH({0})", 1),
        "len": ("LENGTH({0})", 1),
        "instr": ("INSTR({0}, {1})", 2),
        "instrrev": ("INSTR({0}, {1}, -1)", 2),
        "replace": ("REPLACE({0}, {1}, {2})", 3),
        "space": ("RPAD(' ', {0})", 1),
        "replicate": ("RPAD({0}, LENGTH({0}) * {1}, {0})", 2),
        "replicatestring": ("RPAD({0}, LENGTH({0}) * {1}, {0})", 2),
        "chr": ("CHR({0})", 1),
        "asc": ("ASCII({0})", 1),
        "val": ("TO_NUMBER({0})", 1),
        "str": ("TO_CHAR({0})", 1),
        "strreverse": ("REVERSE({0})", 1),
        "strcmp": ("CASE WHEN {0} < {1} THEN -1 WHEN {0} > {1} THEN 1 ELSE 0 END", 2),
        "propercase": ("INITCAP({0})", 1),

        # Date functions
        "currentdate": ("TRUNC(SYSDATE)", 0),
        "currentdatetime": ("SYSTIMESTAMP", 0),
        "currenttime": ("TO_CHAR(SYSDATE, 'HH24:MI:SS')", 0),
        "date": ("TRUNC({0})", 1),
        "year": ("EXTRACT(YEAR FROM {0})", 1),
        "month": ("EXTRACT(MONTH FROM {0})", 1),
        "day": ("EXTRACT(DAY FROM {0})", 1),
        "hour": ("EXTRACT(HOUR FROM CAST({0} AS TIMESTAMP))", 1),
        "minute": ("EXTRACT(MINUTE FROM CAST({0} AS TIMESTAMP))", 1),
        "second": ("EXTRACT(SECOND FROM CAST({0} AS TIMESTAMP))", 1),
        "dayofweek": ("TO_NUMBER(TO_CHAR({0}, 'D'))", 1),
        "weekday": ("TO_CHAR({0}, 'D')", 1),
        "monthname": ("TO_CHAR({0}, 'Month')", 1),
        "dateserial": ("TO_DATE({0}||'-'||{1}||'-'||{2}, 'YYYY-MM-DD')", 3),
        "datevalue": ("TO_DATE({0}, 'YYYY-MM-DD')", 1),
        "timevalue": ("TO_DATE({0}, 'HH24:MI:SS')", 1),
        "now": ("SYSDATE", 0),
        "today": ("TRUNC(SYSDATE)", 0),
        "timer": ("(SYSDATE - TRUNC(SYSDATE)) * 86400", 0),

        # Date arithmetic
        "dateadd": ("({1} + NUMTODSINTERVAL({2}, '{0}'))", 3),  # Special handling needed
        "datediff": ("({2} - {1})", 3),  # Returns days; interval type ignored

        # Numeric functions
        "abs": ("ABS({0})", 1),
        "round": ("ROUND({0}, {1})", 2),
        "truncate": ("TRUNC({0}, {1})", 2),
        "int": ("FLOOR({0})", 1),
        "fix": ("TRUNC({0})", 1),
        "mod": ("MOD({0}, {1})", 2),
        "remainder": ("REMAINDER({0}, {1})", 2),
        "sgn": ("SIGN({0})", 1),
        "sign": ("SIGN({0})", 1),
        "sqrt": ("SQRT({0})", 1),
        "sqr": ("SQRT({0})", 1),
        "exp": ("EXP({0})", 1),
        "log": ("LN({0})", 1),
        "log10": ("LOG(10, {0})", 1),
        "power": ("POWER({0}, {1})", 2),
        "ceiling": ("CEIL({0})", 1),
        "floor": ("FLOOR({0})", 1),

        # Trigonometric functions
        "sin": ("SIN({0})", 1),
        "cos": ("COS({0})", 1),
        "tan": ("TAN({0})", 1),
        "asin": ("ASIN({0})", 1),
        "acos": ("ACOS({0})", 1),
        "atan": ("ATAN({0})", 1),
        "atn": ("ATAN({0})", 1),

        # Conversion functions
        "totext": ("TO_CHAR({0})", 1),
        "tonumber": ("TO_NUMBER({0})", 1),
        "towords": ("TO_CHAR(TO_DATE({0}, 'J'), 'JSP')", 1),  # Approximate
        "cstr": ("TO_CHAR({0})", 1),
        "cdbl": ("TO_NUMBER({0})", 1),
        "cdate": ("TO_DATE({0})", 1),
        "cbool": ("CASE WHEN {0} THEN 'Y' ELSE 'N' END", 1),

        # Null handling
        "isnull": ("({0} IS NULL)", 1),
        "isnothing": ("({0} IS NULL)", 1),
        "nv": ("NVL({0}, {1})", 2),  # Crystal's null value function

        # Logical functions
        "iif": ("CASE WHEN {0} THEN {1} ELSE {2} END", 3),
        "switch": (None, -1),  # Special handling
        "choose": (None, -1),  # Special handling

        # Aggregate functions (for reference in formulas)
        "sum": ("SUM({0})", 1),
        "avg": ("AVG({0})", 1),
        "average": ("AVG({0})", 1),
        "count": ("COUNT({0})", 1),
        "max": ("MAX({0})", 1),
        "maximum": ("MAX({0})", 1),
        "min": ("MIN({0})", 1),
        "minimum": ("MIN({0})", 1),
        "distinctcount": ("COUNT(DISTINCT {0})", 1),
    }

    # Crystal operators to Oracle operators
    OPERATOR_MAP = {
        "&": "||",  # String concatenation
        "And": "AND",
        "Or": "OR",
        "Not": "NOT",
        "Xor": "XOR",  # Note: Oracle doesn't have XOR, may need special handling
        "<>": "!=",
        "=": "=",
        "Mod": "MOD",
        "\\": "TRUNC(? / ?)",  # Integer division
    }

    def __init__(
        self,
        formula_prefix: str = "CF_",
        on_unsupported: str = "placeholder",
    ):
        """Initialize the formula translator.

        Args:
            formula_prefix: Prefix for Oracle formula names.
            on_unsupported: Action for unsupported formulas ('placeholder', 'skip', 'fail').
        """
        self.formula_prefix = formula_prefix
        self.on_unsupported = on_unsupported
        self.logger = get_logger("formula_translator")
        self.error_handler = ErrorHandler()

    def translate(self, formula: Formula) -> TranslatedFormula:
        """Translate a Crystal formula to PL/SQL.

        Args:
            formula: The Crystal formula to translate.

        Returns:
            TranslatedFormula with PL/SQL code.
        """
        self.logger.debug(f"Translating formula: {formula.name}")

        oracle_name = self._make_oracle_name(formula.name)
        warnings = []

        try:
            # Get expression text
            expression = formula.expression.strip()

            if not expression:
                # Empty formula
                return TranslatedFormula(
                    original_name=formula.name,
                    oracle_name=oracle_name,
                    plsql_code="RETURN NULL;",
                    return_type=self._get_return_type(formula.return_type),
                    success=True,
                    warnings=["Empty formula converted to NULL"],
                )

            # Translate the expression
            plsql_expr, expr_warnings = self._translate_expression(expression)
            warnings.extend(expr_warnings)

            # Build function body
            return_type = self._get_return_type(formula.return_type)
            plsql_code = self._build_function_body(
                oracle_name, return_type, plsql_expr
            )

            # Extract column references
            columns = self._extract_column_references(plsql_expr)

            return TranslatedFormula(
                original_name=formula.name,
                oracle_name=oracle_name,
                plsql_code=plsql_code,
                return_type=return_type,
                success=True,
                warnings=warnings,
                referenced_columns=columns,
            )

        except Exception as e:
            self.logger.warning(f"Failed to translate formula {formula.name}: {e}")

            if self.on_unsupported == "placeholder":
                placeholder = self._create_placeholder(formula, oracle_name, str(e))
                return placeholder
            elif self.on_unsupported == "skip":
                return TranslatedFormula(
                    original_name=formula.name,
                    oracle_name=oracle_name,
                    plsql_code="",
                    return_type="VARCHAR2",
                    success=False,
                    warnings=[f"Skipped: {str(e)}"],
                )
            else:
                raise

    def _translate_expression(self, expression: str) -> tuple[str, list[str]]:
        """Translate a Crystal expression to Oracle SQL/PL/SQL.

        Args:
            expression: Crystal formula expression.

        Returns:
            Tuple of (translated expression, list of warnings).
        """
        warnings = []
        result = expression

        # Handle multi-line expressions
        result = result.replace("\r\n", "\n").replace("\r", "\n")

        # Step 1: Convert field references {Table.Field} -> column names
        result = self._convert_field_references(result)

        # Step 2: Convert formula references @Formula -> CF_FORMULA()
        result = self._convert_formula_references(result)

        # Step 3: Convert parameter references ?Param -> :P_PARAM
        result = self._convert_parameter_references(result)

        # Step 4: Convert string concatenation & -> ||
        result = self._convert_operators(result)

        # Step 5: Convert function calls
        result, func_warnings = self._convert_functions(result)
        warnings.extend(func_warnings)

        # Step 6: Convert IIF to CASE WHEN
        result = self._convert_iif(result)

        # Step 7: Clean up
        result = self._cleanup_expression(result)

        return result, warnings

    def _convert_field_references(self, expression: str) -> str:
        """Convert Crystal field references to Oracle column names.

        {Table.Field} -> FIELD_NAME or TABLE_FIELD
        """
        def replace_field(match):
            field_ref = match.group(1)
            # Remove table prefix and convert to uppercase
            if "." in field_ref:
                parts = field_ref.split(".")
                column_name = parts[-1].upper()
            else:
                column_name = field_ref.upper()
            # Replace spaces with underscores
            column_name = column_name.replace(" ", "_")
            return f":{column_name}"

        # Pattern for {Table.Field} but not {@Formula} or {?Parameter}
        pattern = r"\{([^@?}][^}]*)\}"
        return re.sub(pattern, replace_field, expression)

    def _convert_formula_references(self, expression: str) -> str:
        """Convert Crystal formula references to Oracle function calls.

        @FormulaName or {@FormulaName} -> CF_FORMULANAME()
        """
        def replace_formula(match):
            formula_name = match.group(1)
            oracle_name = self._make_oracle_name(formula_name)
            return f"{oracle_name}()"

        # Pattern for {@FormulaName}
        result = re.sub(r"\{@([^}]+)\}", replace_formula, expression)

        # Pattern for @FormulaName (not in braces)
        result = re.sub(r"@(\w+)", replace_formula, result)

        return result

    def _convert_parameter_references(self, expression: str) -> str:
        """Convert Crystal parameter references to Oracle bind variables.

        ?ParamName or {?ParamName} -> :P_PARAMNAME
        """
        def replace_param(match):
            param_name = match.group(1)
            oracle_name = f"P_{param_name.upper().replace(' ', '_')}"
            return f":{oracle_name}"

        # Pattern for {?ParamName}
        result = re.sub(r"\{\?([^}]+)\}", replace_param, expression)

        # Pattern for ?ParamName (not in braces)
        result = re.sub(r"\?(\w+)", replace_param, result)

        return result

    def _convert_operators(self, expression: str) -> str:
        """Convert Crystal operators to Oracle operators."""
        result = expression

        for crystal_op, oracle_op in self.OPERATOR_MAP.items():
            if crystal_op == "&":
                # String concatenation - be careful not to replace && or &=
                result = re.sub(r"(?<![&=])&(?![&=])", oracle_op, result)
            else:
                # Word operators need word boundaries
                result = re.sub(
                    rf"\b{re.escape(crystal_op)}\b",
                    oracle_op,
                    result,
                    flags=re.IGNORECASE,
                )

        return result

    def _convert_functions(self, expression: str) -> tuple[str, list[str]]:
        """Convert Crystal function calls to Oracle equivalents."""
        warnings = []
        result = expression

        # Find all function calls: FunctionName(args)
        pattern = r"\b(\w+)\s*\(([^)]*)\)"

        def replace_function(match):
            func_name = match.group(1).lower()
            args_str = match.group(2)

            # Special handling for DatePart
            if func_name == "datepart":
                return self._convert_datepart(args_str, warnings)

            # Special handling for RunningTotal
            if func_name == "runningtotal":
                warnings.append("RunningTotal requires manual conversion - using SUM() OVER()")
                return f"SUM({args_str}) OVER (ORDER BY ROWNUM)"

            if func_name in self.FUNCTION_MAP:
                template, expected_args = self.FUNCTION_MAP[func_name]

                if template is None:
                    # Special handling needed
                    warnings.append(f"Function '{func_name}' requires manual conversion")
                    return match.group(0)

                if expected_args == 0:
                    return template

                # Parse arguments
                args = self._parse_function_args(args_str)

                if expected_args > 0 and len(args) != expected_args:
                    warnings.append(
                        f"Function '{func_name}' expected {expected_args} args, got {len(args)}"
                    )

                try:
                    return template.format(*args)
                except (IndexError, KeyError):
                    warnings.append(f"Could not format function '{func_name}'")
                    return match.group(0)

            # Unknown function - pass through but warn
            if func_name not in ["sum", "avg", "count", "max", "min"]:
                warnings.append(f"Unknown function '{func_name}' - passed through")
            return match.group(0)

        result = re.sub(pattern, replace_function, result)
        return result, warnings

    def _convert_datepart(self, args_str: str, warnings: list[str]) -> str:
        """Convert DatePart function to appropriate Oracle function.

        DatePart(interval, date) -> EXTRACT or TO_CHAR
        """
        args = self._parse_function_args(args_str)
        if len(args) < 2:
            warnings.append("DatePart requires 2 arguments")
            return f"DatePart({args_str})"

        # Remove quotes from interval if present
        interval = args[0].strip().strip("'\"").lower()
        date_expr = args[1].strip()

        # Map Crystal intervals to Oracle
        interval_map = {
            "yyyy": f"EXTRACT(YEAR FROM {date_expr})",
            "year": f"EXTRACT(YEAR FROM {date_expr})",
            "q": f"TO_CHAR({date_expr}, 'Q')",
            "quarter": f"TO_CHAR({date_expr}, 'Q')",
            "m": f"EXTRACT(MONTH FROM {date_expr})",
            "month": f"EXTRACT(MONTH FROM {date_expr})",
            "d": f"EXTRACT(DAY FROM {date_expr})",
            "day": f"EXTRACT(DAY FROM {date_expr})",
            "y": f"TO_CHAR({date_expr}, 'DDD')",
            "dayofyear": f"TO_CHAR({date_expr}, 'DDD')",
            "w": f"TO_CHAR({date_expr}, 'IW')",
            "week": f"TO_CHAR({date_expr}, 'IW')",
            "ww": f"TO_CHAR({date_expr}, 'IW')",
            "weekday": f"TO_CHAR({date_expr}, 'D')",
            "h": f"EXTRACT(HOUR FROM CAST({date_expr} AS TIMESTAMP))",
            "hour": f"EXTRACT(HOUR FROM CAST({date_expr} AS TIMESTAMP))",
            "n": f"EXTRACT(MINUTE FROM CAST({date_expr} AS TIMESTAMP))",
            "minute": f"EXTRACT(MINUTE FROM CAST({date_expr} AS TIMESTAMP))",
            "s": f"EXTRACT(SECOND FROM CAST({date_expr} AS TIMESTAMP))",
            "second": f"EXTRACT(SECOND FROM CAST({date_expr} AS TIMESTAMP))",
        }

        if interval in interval_map:
            return interval_map[interval]
        else:
            warnings.append(f"Unknown DatePart interval '{interval}'")
            return f"DatePart({args_str})"

    def _convert_iif(self, expression: str) -> str:
        """Convert nested IIF statements to CASE WHEN.

        IIF(cond, true_val, false_val) -> CASE WHEN cond THEN true_val ELSE false_val END
        """
        # Handle nested IIF by working from innermost out
        pattern = r"\bIIF\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)"

        max_iterations = 20  # Prevent infinite loops
        for _ in range(max_iterations):
            new_result = re.sub(
                pattern,
                r"CASE WHEN \1 THEN \2 ELSE \3 END",
                expression,
                flags=re.IGNORECASE,
            )
            if new_result == expression:
                break
            expression = new_result

        return expression

    def _parse_function_args(self, args_str: str) -> list[str]:
        """Parse function arguments, handling nested parentheses."""
        if not args_str.strip():
            return []

        args = []
        current_arg = ""
        depth = 0

        for char in args_str:
            if char == "(":
                depth += 1
                current_arg += char
            elif char == ")":
                depth -= 1
                current_arg += char
            elif char == "," and depth == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char

        if current_arg.strip():
            args.append(current_arg.strip())

        return args

    def _cleanup_expression(self, expression: str) -> str:
        """Clean up the translated expression."""
        result = expression

        # Remove Crystal-specific comments
        result = re.sub(r"//.*$", "", result, flags=re.MULTILINE)

        # Normalize whitespace
        result = re.sub(r"\s+", " ", result)
        result = result.strip()

        return result

    def _make_oracle_name(self, name: str) -> str:
        """Create Oracle-compatible formula name."""
        # Remove @ prefix if present
        if name.startswith("@"):
            name = name[1:]

        # Replace invalid characters
        oracle_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure starts with letter
        if oracle_name and oracle_name[0].isdigit():
            oracle_name = "F_" + oracle_name

        # Add prefix
        if not oracle_name.upper().startswith(self.formula_prefix.upper()):
            oracle_name = self.formula_prefix + oracle_name

        return oracle_name.upper()

    def _get_return_type(self, data_type: DataType) -> str:
        """Get Oracle return type for formula."""
        type_map = {
            DataType.STRING: "VARCHAR2",
            DataType.NUMBER: "NUMBER",
            DataType.CURRENCY: "NUMBER",
            DataType.DATE: "DATE",
            DataType.DATETIME: "TIMESTAMP",
            DataType.BOOLEAN: "VARCHAR2",
            DataType.MEMO: "CLOB",
        }
        return type_map.get(data_type, "VARCHAR2")

    def _build_function_body(
        self,
        name: str,
        return_type: str,
        expression: str,
    ) -> str:
        """Build complete PL/SQL function body."""
        return f"""function {name} return {return_type} is
begin
  return ({expression});
end {name};"""

    def _create_placeholder(
        self,
        formula: Formula,
        oracle_name: str,
        error_message: str,
    ) -> TranslatedFormula:
        """Create a placeholder function for unsupported formulas."""
        return_type = self._get_return_type(formula.return_type)

        # Create a commented placeholder
        original = formula.expression.replace("*/", "* /")  # Escape comment terminators
        plsql_code = f"""function {oracle_name} return {return_type} is
  -- TODO: Manual conversion required
  -- Original Crystal formula:
  -- {original[:500]}
  -- Error: {error_message}
begin
  -- Placeholder: Replace with actual implementation
  return NULL;
end {oracle_name};"""

        return TranslatedFormula(
            original_name=formula.name,
            oracle_name=oracle_name,
            plsql_code=plsql_code,
            return_type=return_type,
            success=True,
            is_placeholder=True,
            warnings=[
                f"Created placeholder - manual conversion required: {error_message}"
            ],
        )

    def _extract_column_references(self, expression: str) -> list[str]:
        """Extract Oracle column references from translated expression."""
        # Find :COLUMN_NAME patterns
        pattern = r":([A-Z_][A-Z0-9_]*)"
        matches = re.findall(pattern, expression)
        return list(set(matches))

    def batch_translate(self, formulas: list[Formula]) -> list[TranslatedFormula]:
        """Translate multiple formulas.

        Args:
            formulas: List of Crystal formulas.

        Returns:
            List of translated formulas.
        """
        results = []
        for formula in formulas:
            result = self.translate(formula)
            results.append(result)

        # Log summary
        successful = sum(1 for r in results if r.success and not r.is_placeholder)
        placeholders = sum(1 for r in results if r.is_placeholder)
        failed = sum(1 for r in results if not r.success)

        self.logger.info(
            f"Formula translation: {successful} successful, "
            f"{placeholders} placeholders, {failed} failed"
        )

        return results
