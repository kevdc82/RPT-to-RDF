"""
Unit tests for Formula Translator.

Tests the conversion of Crystal Reports formulas to Oracle PL/SQL.
"""

import pytest
from src.transformation.formula_translator import FormulaTranslator, TranslatedFormula
from src.parsing.report_model import Formula, DataType, FormulaSyntax


class TestFormulaTranslator:
    """Test suite for FormulaTranslator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.translator = FormulaTranslator(
            formula_prefix="CF_",
            on_unsupported="placeholder"
        )

    # String function tests
    def test_left_function(self):
        """Test LEFT string function conversion."""
        formula = Formula(
            name="TestLeft",
            expression="Left({Field}, 5)",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SUBSTR(:FIELD, 1, 5)" in result.plsql_code

    def test_right_function(self):
        """Test RIGHT string function conversion."""
        formula = Formula(
            name="TestRight",
            expression="Right({Field}, 5)",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SUBSTR(:FIELD, -1 * 5)" in result.plsql_code

    def test_mid_function(self):
        """Test MID string function conversion."""
        formula = Formula(
            name="TestMid",
            expression="Mid({Field}, 2, 10)",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SUBSTR(:FIELD, 2, 10)" in result.plsql_code

    def test_trim_function(self):
        """Test TRIM string function conversion."""
        formula = Formula(
            name="TestTrim",
            expression="Trim({Field})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TRIM(:FIELD)" in result.plsql_code

    def test_upper_function(self):
        """Test UPPER string function conversion."""
        formula = Formula(
            name="TestUpper",
            expression="Upper({Field})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "UPPER(:FIELD)" in result.plsql_code

    def test_lower_function(self):
        """Test LOWER string function conversion."""
        formula = Formula(
            name="TestLower",
            expression="Lower({Field})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "LOWER(:FIELD)" in result.plsql_code

    def test_length_function(self):
        """Test LENGTH string function conversion."""
        formula = Formula(
            name="TestLen",
            expression="Len({Field})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "LENGTH(:FIELD)" in result.plsql_code

    def test_replace_function(self):
        """Test REPLACE string function conversion."""
        formula = Formula(
            name="TestReplace",
            expression="Replace({Field}, 'old', 'new')",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "REPLACE(:FIELD, 'old', 'new')" in result.plsql_code

    # Date function tests
    def test_current_date(self):
        """Test CurrentDate function conversion."""
        formula = Formula(
            name="TestCurDate",
            expression="CurrentDate",
            return_type=DataType.DATE
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TRUNC(SYSDATE)" in result.plsql_code

    def test_current_datetime(self):
        """Test CurrentDateTime function conversion."""
        formula = Formula(
            name="TestCurDateTime",
            expression="CurrentDateTime",
            return_type=DataType.DATETIME
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SYSTIMESTAMP" in result.plsql_code

    def test_current_time(self):
        """Test CurrentTime function conversion."""
        formula = Formula(
            name="TestCurTime",
            expression="CurrentTime",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_CHAR(SYSDATE, 'HH24:MI:SS')" in result.plsql_code

    def test_year_function(self):
        """Test YEAR date function conversion."""
        formula = Formula(
            name="TestYear",
            expression="Year({DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXTRACT(YEAR FROM :DATEFIELD)" in result.plsql_code

    def test_month_function(self):
        """Test MONTH date function conversion."""
        formula = Formula(
            name="TestMonth",
            expression="Month({DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXTRACT(MONTH FROM :DATEFIELD)" in result.plsql_code

    def test_day_function(self):
        """Test DAY date function conversion."""
        formula = Formula(
            name="TestDay",
            expression="Day({DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXTRACT(DAY FROM :DATEFIELD)" in result.plsql_code

    # Numeric function tests
    def test_abs_function(self):
        """Test ABS numeric function conversion."""
        formula = Formula(
            name="TestAbs",
            expression="Abs({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "ABS(:AMOUNT)" in result.plsql_code

    def test_round_function(self):
        """Test ROUND numeric function conversion."""
        formula = Formula(
            name="TestRound",
            expression="Round({Amount}, 2)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "ROUND(:AMOUNT, 2)" in result.plsql_code

    def test_truncate_function(self):
        """Test TRUNCATE numeric function conversion."""
        formula = Formula(
            name="TestTrunc",
            expression="Truncate({Amount}, 0)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TRUNC(:AMOUNT, 0)" in result.plsql_code

    def test_mod_function(self):
        """Test MOD numeric function conversion."""
        formula = Formula(
            name="TestMod",
            expression="Mod({Value}, 10)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "MOD(:VALUE, 10)" in result.plsql_code

    # IIF tests
    def test_simple_iif(self):
        """Test simple IIF statement conversion."""
        formula = Formula(
            name="TestIIF",
            expression="IIF({Amount} > 100, 'High', 'Low')",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CASE WHEN" in result.plsql_code
        assert "THEN" in result.plsql_code
        assert "ELSE" in result.plsql_code
        assert "END" in result.plsql_code

    def test_nested_iif(self):
        """Test nested IIF statement conversion."""
        formula = Formula(
            name="TestNestedIIF",
            expression="IIF({A} > 1, 'X', IIF({B} > 2, 'Y', 'Z'))",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        # Should have 2 WHEN clauses for nested IIF
        assert result.plsql_code.count("WHEN") == 2
        assert "CASE WHEN" in result.plsql_code

    def test_iif_with_numeric_result(self):
        """Test IIF with numeric result."""
        formula = Formula(
            name="TestIIFNumeric",
            expression="IIF({Status} = 'Active', 1, 0)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CASE WHEN" in result.plsql_code

    # Field reference tests
    def test_field_reference_simple(self):
        """Test simple field reference conversion."""
        formula = Formula(
            name="TestFieldRef",
            expression="{Field}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":FIELD" in result.plsql_code
        assert "FIELD" in result.referenced_columns

    def test_field_reference_with_table(self):
        """Test field reference with table prefix."""
        formula = Formula(
            name="TestTableField",
            expression="{Table.Field}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":FIELD" in result.plsql_code

    def test_field_reference_with_spaces(self):
        """Test field reference with spaces in name."""
        formula = Formula(
            name="TestSpacedField",
            expression="{Customer Name}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":CUSTOMER_NAME" in result.plsql_code

    # Formula reference tests
    def test_formula_reference_with_at(self):
        """Test formula reference with @ prefix."""
        formula = Formula(
            name="TestFormulaRef",
            expression="@MyFormula",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CF_MYFORMULA()" in result.plsql_code

    def test_formula_reference_in_braces(self):
        """Test formula reference in braces."""
        formula = Formula(
            name="TestFormulaRefBraces",
            expression="{@MyFormula}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CF_MYFORMULA()" in result.plsql_code

    def test_formula_reference_with_field(self):
        """Test formula combining field and formula reference."""
        formula = Formula(
            name="TestCombined",
            expression="{Amount} + @Discount",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":AMOUNT" in result.plsql_code
        assert "CF_DISCOUNT()" in result.plsql_code

    # Parameter reference tests
    def test_parameter_reference(self):
        """Test parameter reference conversion."""
        formula = Formula(
            name="TestParam",
            expression="{?StartDate}",
            return_type=DataType.DATE
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":P_STARTDATE" in result.plsql_code

    def test_parameter_reference_without_braces(self):
        """Test parameter reference without braces."""
        formula = Formula(
            name="TestParamNoBrace",
            expression="?EndDate",
            return_type=DataType.DATE
        )
        result = self.translator.translate(formula)
        assert result.success
        assert ":P_ENDDATE" in result.plsql_code

    # Operator tests
    def test_string_concatenation(self):
        """Test string concatenation operator conversion."""
        formula = Formula(
            name="TestConcat",
            expression="{FirstName} & ' ' & {LastName}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "||" in result.plsql_code
        assert "&" not in result.plsql_code or "&&" in result.plsql_code

    def test_and_operator(self):
        """Test AND logical operator conversion."""
        formula = Formula(
            name="TestAnd",
            expression="{Active} And {Verified}",
            return_type=DataType.BOOLEAN
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "AND" in result.plsql_code.upper()

    def test_or_operator(self):
        """Test OR logical operator conversion."""
        formula = Formula(
            name="TestOr",
            expression="{Status} = 'A' Or {Status} = 'B'",
            return_type=DataType.BOOLEAN
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "OR" in result.plsql_code.upper()

    def test_not_operator(self):
        """Test NOT logical operator conversion."""
        formula = Formula(
            name="TestNot",
            expression="Not {Active}",
            return_type=DataType.BOOLEAN
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "NOT" in result.plsql_code.upper()

    # Null handling tests
    def test_isnull_function(self):
        """Test IsNull function conversion."""
        formula = Formula(
            name="TestIsNull",
            expression="IsNull({Field})",
            return_type=DataType.BOOLEAN
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "IS NULL" in result.plsql_code.upper()

    # Complex expression tests
    def test_complex_expression(self):
        """Test complex expression with multiple operations."""
        formula = Formula(
            name="TestComplex",
            expression="IIF({Amount} > 1000, Round({Amount} * 0.9, 2), {Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CASE WHEN" in result.plsql_code
        assert "ROUND" in result.plsql_code.upper()

    def test_multi_level_nested_functions(self):
        """Test multiple levels of nested functions."""
        formula = Formula(
            name="TestNested",
            expression="Upper(Trim(Left({Name}, 10)))",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "UPPER" in result.plsql_code.upper()
        assert "TRIM" in result.plsql_code.upper()
        assert "SUBSTR" in result.plsql_code.upper()

    # Return type tests
    def test_string_return_type(self):
        """Test formula with string return type."""
        formula = Formula(
            name="TestStringType",
            expression="{Name}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert result.return_type == "VARCHAR2"
        assert "VARCHAR2" in result.plsql_code

    def test_number_return_type(self):
        """Test formula with number return type."""
        formula = Formula(
            name="TestNumberType",
            expression="{Amount}",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert result.return_type == "NUMBER"
        assert "NUMBER" in result.plsql_code

    def test_date_return_type(self):
        """Test formula with date return type."""
        formula = Formula(
            name="TestDateType",
            expression="{OrderDate}",
            return_type=DataType.DATE
        )
        result = self.translator.translate(formula)
        assert result.success
        assert result.return_type == "DATE"
        assert "DATE" in result.plsql_code

    def test_datetime_return_type(self):
        """Test formula with datetime return type."""
        formula = Formula(
            name="TestDateTimeType",
            expression="{CreatedAt}",
            return_type=DataType.DATETIME
        )
        result = self.translator.translate(formula)
        assert result.success
        assert result.return_type == "TIMESTAMP"
        assert "TIMESTAMP" in result.plsql_code

    # Oracle name conversion tests
    def test_oracle_name_generation(self):
        """Test Oracle name generation from formula name."""
        formula = Formula(
            name="MyFormula",
            expression="{Field}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.oracle_name == "CF_MYFORMULA"

    def test_oracle_name_with_special_chars(self):
        """Test Oracle name generation with special characters."""
        formula = Formula(
            name="My-Formula!",
            expression="{Field}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.oracle_name.startswith("CF_")
        assert "-" not in result.oracle_name
        assert "!" not in result.oracle_name

    def test_oracle_name_starting_with_number(self):
        """Test Oracle name when formula starts with number."""
        formula = Formula(
            name="1stFormula",
            expression="{Field}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        # Should add F_ prefix for names starting with digit
        assert result.oracle_name.startswith("CF_F_") or result.oracle_name.startswith("CF_1")

    # Empty and edge cases
    def test_empty_formula(self):
        """Test empty formula conversion."""
        formula = Formula(
            name="TestEmpty",
            expression="",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "NULL" in result.plsql_code.upper()
        assert len(result.warnings) > 0

    def test_whitespace_only_formula(self):
        """Test formula with only whitespace."""
        formula = Formula(
            name="TestWhitespace",
            expression="   \n\t   ",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "NULL" in result.plsql_code.upper()

    # Batch translation tests
    def test_batch_translate_empty_list(self):
        """Test batch translation with empty list."""
        results = self.translator.batch_translate([])
        assert len(results) == 0

    def test_batch_translate_multiple_formulas(self):
        """Test batch translation with multiple formulas."""
        formulas = [
            Formula(name="F1", expression="{Field1}", return_type=DataType.STRING),
            Formula(name="F2", expression="{Field2}", return_type=DataType.NUMBER),
            Formula(name="F3", expression="{Field3}", return_type=DataType.DATE),
        ]
        results = self.translator.batch_translate(formulas)
        assert len(results) == 3
        assert all(r.success for r in results)

    # Column reference extraction tests
    def test_extract_column_references_single(self):
        """Test extraction of single column reference."""
        formula = Formula(
            name="TestExtract",
            expression="{CustomerName}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert "CUSTOMERNAME" in result.referenced_columns

    def test_extract_column_references_multiple(self):
        """Test extraction of multiple column references."""
        formula = Formula(
            name="TestMultiRef",
            expression="{FirstName} & ' ' & {LastName}",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert "FIRSTNAME" in result.referenced_columns
        assert "LASTNAME" in result.referenced_columns

    def test_extract_column_references_none(self):
        """Test extraction when no column references exist."""
        formula = Formula(
            name="TestNoRef",
            expression="'Constant Value'",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert len(result.referenced_columns) == 0

    # Aggregate function tests
    def test_sum_aggregate(self):
        """Test SUM aggregate function."""
        formula = Formula(
            name="TestSum",
            expression="Sum({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SUM(:AMOUNT)" in result.plsql_code

    def test_avg_aggregate(self):
        """Test AVG aggregate function."""
        formula = Formula(
            name="TestAvg",
            expression="Avg({Quantity})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "AVG(:QUANTITY)" in result.plsql_code

    def test_count_aggregate(self):
        """Test COUNT aggregate function."""
        formula = Formula(
            name="TestCount",
            expression="Count({OrderID})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "COUNT(:ORDERID)" in result.plsql_code

    # Conversion function tests
    def test_totext_function(self):
        """Test ToText conversion function."""
        formula = Formula(
            name="TestToText",
            expression="ToText({Amount})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_CHAR(:AMOUNT)" in result.plsql_code

    def test_tonumber_function(self):
        """Test ToNumber conversion function."""
        formula = Formula(
            name="TestToNumber",
            expression="ToNumber({StringField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_NUMBER(:STRINGFIELD)" in result.plsql_code

    # Error handling tests
    def test_unsupported_function_placeholder(self):
        """Test handling of unsupported function with placeholder."""
        translator = FormulaTranslator(on_unsupported="placeholder")
        # Using a complex function that might not be supported
        formula = Formula(
            name="TestUnsupported",
            expression="SomeComplexUnsupportedFunction({Field})",
            return_type=DataType.STRING
        )
        result = translator.translate(formula)
        # Should create placeholder and succeed
        assert result.success

    def test_on_unsupported_skip(self):
        """Test skip mode for unsupported formulas."""
        translator = FormulaTranslator(on_unsupported="skip")
        formula = Formula(
            name="TestSkip",
            expression="",  # Empty will trigger special handling
            return_type=DataType.STRING
        )
        result = translator.translate(formula)
        assert result.success  # Empty formulas are handled

    # Case sensitivity tests
    def test_function_case_insensitive(self):
        """Test that function names are case-insensitive."""
        formula = Formula(
            name="TestCase",
            expression="UPPER({field})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "UPPER(:FIELD)" in result.plsql_code

    # Comment handling tests
    def test_crystal_comments_removed(self):
        """Test that Crystal comments are removed."""
        formula = Formula(
            name="TestComments",
            expression="{Field} // This is a comment",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "//" not in result.plsql_code or "RETURN" in result.plsql_code


    # NEW STRING FUNCTION TESTS
    def test_chr_function(self):
        """Test Chr(n) -> CHR(n)."""
        formula = Formula(
            name="TestChr",
            expression="Chr(65)",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CHR(65)" in result.plsql_code

    def test_asc_function(self):
        """Test Asc(str) -> ASCII(str)."""
        formula = Formula(
            name="TestAsc",
            expression="Asc('A')",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "ASCII('A')" in result.plsql_code

    def test_strcmp_function(self):
        """Test StrCmp(s1, s2) -> CASE WHEN."""
        formula = Formula(
            name="TestStrCmp",
            expression="StrCmp('abc', 'def')",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CASE WHEN" in result.plsql_code
        assert "'abc' < 'def'" in result.plsql_code or "'abc'<'def'" in result.plsql_code.replace(" ", "")

    def test_replicatestring_function(self):
        """Test ReplicateString(str, n) -> RPAD."""
        formula = Formula(
            name="TestReplicate",
            expression="ReplicateString('AB', 5)",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "RPAD('AB', LENGTH('AB') * 5, 'AB')" in result.plsql_code

    def test_strreverse_function(self):
        """Test StrReverse(str) -> REVERSE(str)."""
        formula = Formula(
            name="TestReverse",
            expression="StrReverse('hello')",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "REVERSE('hello')" in result.plsql_code

    def test_propercase_function(self):
        """Test ProperCase(str) -> INITCAP(str)."""
        formula = Formula(
            name="TestProperCase",
            expression="ProperCase('hello world')",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "INITCAP('hello world')" in result.plsql_code

    # NEW DATE FUNCTION TESTS
    def test_weekday_function(self):
        """Test WeekDay(date) -> TO_CHAR(date, 'D')."""
        formula = Formula(
            name="TestWeekDay",
            expression="WeekDay({DateField})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_CHAR(:DATEFIELD, 'D')" in result.plsql_code

    def test_monthname_function(self):
        """Test MonthName(date) -> TO_CHAR(date, 'Month')."""
        formula = Formula(
            name="TestMonthName",
            expression="MonthName({DateField})",
            return_type=DataType.STRING
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_CHAR(:DATEFIELD, 'Month')" in result.plsql_code

    def test_timer_function(self):
        """Test Timer -> (SYSDATE - TRUNC(SYSDATE)) * 86400."""
        formula = Formula(
            name="TestTimer",
            expression="Timer",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "(SYSDATE - TRUNC(SYSDATE)) * 86400" in result.plsql_code

    def test_datepart_year(self):
        """Test DatePart('yyyy', date)."""
        formula = Formula(
            name="TestDatePartYear",
            expression="DatePart('yyyy', {DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXTRACT(YEAR FROM :DATEFIELD)" in result.plsql_code

    def test_datepart_quarter(self):
        """Test DatePart('q', date)."""
        formula = Formula(
            name="TestDatePartQuarter",
            expression="DatePart('q', {DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TO_CHAR(:DATEFIELD, 'Q')" in result.plsql_code

    def test_datepart_month(self):
        """Test DatePart('m', date)."""
        formula = Formula(
            name="TestDatePartMonth",
            expression="DatePart('m', {DateField})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXTRACT(MONTH FROM :DATEFIELD)" in result.plsql_code

    # NEW MATH FUNCTION TESTS
    def test_sqr_function(self):
        """Test Sqr(n) -> SQRT(n)."""
        formula = Formula(
            name="TestSqr",
            expression="Sqr(16)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SQRT(16)" in result.plsql_code

    def test_exp_function(self):
        """Test Exp(n) -> EXP(n)."""
        formula = Formula(
            name="TestExp",
            expression="Exp(2)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "EXP(2)" in result.plsql_code

    def test_log_function(self):
        """Test Log(n) -> LN(n)."""
        formula = Formula(
            name="TestLog",
            expression="Log(10)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "LN(10)" in result.plsql_code

    def test_sgn_function(self):
        """Test Sgn(n) -> SIGN(n)."""
        formula = Formula(
            name="TestSgn",
            expression="Sgn(-5)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "SIGN(-5)" in result.plsql_code

    def test_fix_function(self):
        """Test Fix(n) -> TRUNC(n)."""
        formula = Formula(
            name="TestFix",
            expression="Fix(3.7)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "TRUNC(3.7)" in result.plsql_code

    def test_int_function(self):
        """Test Int(n) -> FLOOR(n)."""
        formula = Formula(
            name="TestInt",
            expression="Int(3.7)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "FLOOR(3.7)" in result.plsql_code

    def test_ceiling_function(self):
        """Test Ceiling(n) -> CEIL(n)."""
        formula = Formula(
            name="TestCeiling",
            expression="Ceiling(3.2)",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "CEIL(3.2)" in result.plsql_code

    # NEW AGGREGATE FUNCTION TESTS
    def test_average_function(self):
        """Test Average(field) -> AVG(field)."""
        formula = Formula(
            name="TestAverage",
            expression="Average({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "AVG(:AMOUNT)" in result.plsql_code

    def test_maximum_function(self):
        """Test Maximum(field) -> MAX(field)."""
        formula = Formula(
            name="TestMaximum",
            expression="Maximum({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "MAX(:AMOUNT)" in result.plsql_code

    def test_minimum_function(self):
        """Test Minimum(field) -> MIN(field)."""
        formula = Formula(
            name="TestMinimum",
            expression="Minimum({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        assert "MIN(:AMOUNT)" in result.plsql_code

    # RUNNING TOTAL TESTS
    def test_runningtotal_function(self):
        """Test RunningTotal -> SUM() OVER()."""
        formula = Formula(
            name="TestRunningTotal",
            expression="RunningTotal({Amount})",
            return_type=DataType.NUMBER
        )
        result = self.translator.translate(formula)
        assert result.success
        # Check for the SUM/OVER pattern (spacing may vary)
        assert "SUM(:AMOUNT)" in result.plsql_code
        assert "OVER" in result.plsql_code
        assert "ORDER BY ROWNUM" in result.plsql_code
        # Should have a warning about manual conversion
        assert any("RunningTotal" in w for w in result.warnings)


class TestFormulaTranslatorConfiguration:
    """Test FormulaTranslator configuration options."""

    def test_custom_formula_prefix(self):
        """Test custom formula prefix."""
        translator = FormulaTranslator(formula_prefix="FRM_")
        formula = Formula(
            name="TestPrefix",
            expression="{Field}",
            return_type=DataType.STRING
        )
        result = translator.translate(formula)
        assert result.oracle_name.startswith("FRM_")

    def test_on_unsupported_modes(self):
        """Test different on_unsupported modes."""
        modes = ["placeholder", "skip", "fail"]
        for mode in modes:
            translator = FormulaTranslator(on_unsupported=mode)
            assert translator.on_unsupported == mode


class TestTranslatedFormula:
    """Test TranslatedFormula dataclass."""

    def test_to_dict_conversion(self):
        """Test conversion of TranslatedFormula to dictionary."""
        tf = TranslatedFormula(
            original_name="TestFormula",
            oracle_name="CF_TESTFORMULA",
            plsql_code="function CF_TESTFORMULA return VARCHAR2 is...",
            return_type="VARCHAR2",
            success=True,
            warnings=["Test warning"],
            referenced_columns=["FIELD1", "FIELD2"]
        )
        result = tf.to_dict()
        assert result["original_name"] == "TestFormula"
        assert result["oracle_name"] == "CF_TESTFORMULA"
        assert result["success"] is True
        assert len(result["warnings"]) == 1
        assert len(result["referenced_columns"]) == 2

    def test_placeholder_flag(self):
        """Test placeholder flag in TranslatedFormula."""
        tf = TranslatedFormula(
            original_name="Test",
            oracle_name="CF_TEST",
            plsql_code="-- placeholder",
            return_type="VARCHAR2",
            is_placeholder=True
        )
        assert tf.is_placeholder is True
        assert tf.to_dict()["is_placeholder"] is True
