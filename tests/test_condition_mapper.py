"""
Unit tests for ConditionMapper.

Tests the conversion of Crystal Reports conditions to Oracle format triggers.
"""

import pytest

from src.parsing.report_model import FormatSpec
from src.transformation.condition_mapper import ConditionMapper, FormatTrigger


class TestConditionMapper:
    """Test suite for ConditionMapper."""

    @pytest.fixture
    def mapper(self):
        """Create a ConditionMapper instance."""
        return ConditionMapper(trigger_prefix="FT_")

    def test_initialization(self, mapper):
        """Test that mapper initializes correctly."""
        assert mapper.trigger_prefix == "FT_"
        assert mapper._trigger_counter == 0

    def test_convert_simple_suppress_condition(self, mapper):
        """Test converting a simple suppress condition."""
        condition = "{AMOUNT} > 100"
        trigger = mapper.convert_suppress_condition(condition, "AMOUNT_FIELD")

        assert isinstance(trigger, FormatTrigger)
        assert trigger.name == "FT_SUPPRESS_AMOUNT_FIELD"
        assert trigger.trigger_type == "suppress"
        assert ":AMOUNT > 100" in trigger.plsql_code
        assert "function FT_SUPPRESS_AMOUNT_FIELD return boolean is" in trigger.plsql_code
        assert trigger.original_condition == condition

    def test_convert_suppress_with_and_or(self, mapper):
        """Test converting suppress condition with AND/OR operators."""
        condition = "{AMOUNT} > 100 and {STATUS} = 'Active' or {TOTAL} < 50"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":AMOUNT > 100 AND :STATUS = 'Active' OR :TOTAL < 50" in trigger.plsql_code

    def test_convert_field_references(self, mapper):
        """Test field reference conversion from {table.field} to :FIELD."""
        condition = "{orders.amount} > {customers.credit_limit}"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":AMOUNT" in trigger.plsql_code
        assert ":CREDIT_LIMIT" in trigger.plsql_code

    def test_convert_operators(self, mapper):
        """Test operator conversion."""
        test_cases = [
            ("{FIELD} = 100", ":FIELD = 100"),
            ("{FIELD} <> 100", ":FIELD != 100"),
            ("{FIELD} >= 100", ":FIELD >= 100"),
            ("{FIELD} <= 100", ":FIELD <= 100"),
        ]

        for crystal, expected in test_cases:
            trigger = mapper.convert_suppress_condition(crystal)
            assert expected in trigger.plsql_code

    def test_convert_is_null(self, mapper):
        """Test IS NULL conversion."""
        condition = "{FIELD} is null"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":FIELD IS NULL" in trigger.plsql_code

    def test_convert_is_not_null(self, mapper):
        """Test IS NOT NULL conversion."""
        condition = "{FIELD} is not null"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":FIELD IS NOT NULL" in trigger.plsql_code

    def test_convert_boolean_literals(self, mapper):
        """Test boolean literal conversion."""
        condition = "true and false"
        trigger = mapper.convert_suppress_condition(condition)

        assert "TRUE AND FALSE" in trigger.plsql_code

    def test_convert_functions(self, mapper):
        """Test function conversion."""
        test_cases = [
            ("trim({NAME})", "TRIM(:NAME)"),
            ("upper({NAME})", "UPPER(:NAME)"),
            ("lower({NAME})", "LOWER(:NAME)"),
            ("len({NAME})", "LENGTH(:NAME)"),
        ]

        for crystal, expected in test_cases:
            trigger = mapper.convert_suppress_condition(crystal)
            assert expected in trigger.plsql_code

    def test_convert_string_concatenation(self, mapper):
        """Test string concatenation conversion."""
        condition = "{FIRST_NAME} & {LAST_NAME}"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":FIRST_NAME || :LAST_NAME" in trigger.plsql_code

    def test_convert_conditional_format(self, mapper):
        """Test conditional format conversion."""
        condition = "{AMOUNT} > 1000"
        format_spec = {"color": "red", "bold": True}
        trigger = mapper.convert_conditional_format(condition, format_spec, "AMOUNT")

        assert trigger.trigger_type == "conditional_format"
        assert ":AMOUNT > 1000" in trigger.plsql_code
        assert len(trigger.warnings) > 0  # Should warn about limited capabilities

    def test_suppress_if_zero(self, mapper):
        """Test suppress_if_zero conversion."""
        format_spec = FormatSpec(suppress_if_zero=True, suppress_if_blank=False)
        trigger = mapper.convert_suppress_if_conditions(format_spec, "AMOUNT")

        assert trigger is not None
        assert ":AMOUNT = 0" in trigger.plsql_code

    def test_suppress_if_blank(self, mapper):
        """Test suppress_if_blank conversion."""
        format_spec = FormatSpec(suppress_if_zero=False, suppress_if_blank=True)
        trigger = mapper.convert_suppress_if_conditions(format_spec, "NAME")

        assert trigger is not None
        assert ":NAME IS NULL" in trigger.plsql_code
        assert "TRIM" in trigger.plsql_code

    def test_suppress_if_zero_and_blank(self, mapper):
        """Test suppress_if_zero and suppress_if_blank combined."""
        format_spec = FormatSpec(suppress_if_zero=True, suppress_if_blank=True)
        trigger = mapper.convert_suppress_if_conditions(format_spec, "FIELD")

        assert trigger is not None
        assert "OR" in trigger.plsql_code  # Should combine with OR
        assert ":FIELD = 0" in trigger.plsql_code
        assert ":FIELD IS NULL" in trigger.plsql_code

    def test_no_suppress_conditions(self, mapper):
        """Test when no suppress conditions are present."""
        format_spec = FormatSpec(suppress_if_zero=False, suppress_if_blank=False)
        trigger = mapper.convert_suppress_if_conditions(format_spec, "FIELD")

        assert trigger is None

    def test_trigger_counter_increments(self, mapper):
        """Test that trigger counter increments correctly."""
        mapper.convert_suppress_condition("{A} > 1")
        mapper.convert_suppress_condition("{B} > 2")

        assert mapper._trigger_counter == 2

    def test_reset_counter(self, mapper):
        """Test resetting the trigger counter."""
        mapper.convert_suppress_condition("{A} > 1")
        assert mapper._trigger_counter == 1

        mapper.reset_counter()
        assert mapper._trigger_counter == 0

    def test_complex_condition(self, mapper):
        """Test a complex real-world condition."""
        condition = (
            "({orders.status} = 'Pending' or {orders.status} = 'Processing') "
            "and {orders.amount} > 1000 "
            "and {customers.credit_limit} >= {orders.amount}"
        )
        trigger = mapper.convert_suppress_condition(condition, "ORDER_CHECK")

        assert "FT_SUPPRESS_ORDER_CHECK" in trigger.name
        assert ":STATUS = 'Pending'" in trigger.plsql_code
        assert ":STATUS = 'Processing'" in trigger.plsql_code
        assert ":AMOUNT > 1000" in trigger.plsql_code
        assert ":CREDIT_LIMIT >= :AMOUNT" in trigger.plsql_code

    def test_empty_condition(self, mapper):
        """Test handling of empty condition."""
        trigger = mapper.convert_suppress_condition("", "FIELD")

        assert "FALSE" in trigger.plsql_code

    def test_null_comparison_conversion(self, mapper):
        """Test that null comparisons are converted properly."""
        condition = "{FIELD} = null"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":FIELD IS NULL" in trigger.plsql_code
        assert ":FIELD = null" not in trigger.plsql_code.lower()

    def test_not_null_comparison_conversion(self, mapper):
        """Test that not null comparisons are converted properly."""
        condition = "{FIELD} != null"
        trigger = mapper.convert_suppress_condition(condition)

        assert ":FIELD IS NOT NULL" in trigger.plsql_code

    def test_generate_format_trigger_program_unit(self, mapper):
        """Test generating a complete program unit."""
        trigger = FormatTrigger(
            name="TEST_TRIGGER",
            plsql_code="function TEST_TRIGGER return boolean is\nbegin\n  return TRUE;\nend;",
            trigger_type="suppress",
            original_condition="{TEST} = 1",
        )

        program_unit = mapper.generate_format_trigger_program_unit(trigger)
        assert program_unit == trigger.plsql_code

    def test_trigger_name_sanitization(self, mapper):
        """Test that field names with special characters are sanitized."""
        trigger = mapper.convert_suppress_condition(
            "{FIELD} > 1", "Field With Spaces & Special-Chars!"
        )

        # Should replace special characters with underscores
        assert "FT_SUPPRESS_FIELD_WITH_SPACES___SPECIAL_CHARS_" in trigger.name

    def test_case_insensitive_operators(self, mapper):
        """Test that operators work case-insensitively."""
        condition = "{FIELD} AND {OTHER} OR NOT {THIRD}"
        trigger = mapper.convert_suppress_condition(condition)

        assert "AND" in trigger.plsql_code
        assert "OR" in trigger.plsql_code
        assert "NOT" in trigger.plsql_code

    def test_format_trigger_to_dict(self):
        """Test FormatTrigger to_dict method."""
        trigger = FormatTrigger(
            name="TEST",
            plsql_code="code",
            trigger_type="suppress",
            original_condition="test",
            warnings=["warning1"],
        )

        result = trigger.to_dict()
        assert result["name"] == "TEST"
        assert result["plsql_code"] == "code"
        assert result["trigger_type"] == "suppress"
        assert result["original_condition"] == "test"
        assert result["warnings"] == ["warning1"]

    def test_exception_handling_in_trigger(self, mapper):
        """Test that triggers include exception handling."""
        trigger = mapper.convert_suppress_condition("{FIELD} > 1")

        assert "exception" in trigger.plsql_code.lower()
        assert "when others then" in trigger.plsql_code.lower()
        assert "return FALSE" in trigger.plsql_code

    def test_multiple_field_references(self, mapper):
        """Test condition with multiple references to same field."""
        condition = "{AMOUNT} > 100 and {AMOUNT} < 1000"
        trigger = mapper.convert_suppress_condition(condition)

        # Should convert both references
        assert trigger.plsql_code.count(":AMOUNT") == 2


class TestConditionMapperIntegration:
    """Integration tests for ConditionMapper."""

    def test_full_workflow(self):
        """Test complete workflow from condition to PL/SQL."""
        mapper = ConditionMapper(trigger_prefix="FMT_")

        # Create a realistic suppress condition
        crystal_condition = (
            "{invoice.total_amount} > 10000 and "
            "{invoice.status} = 'Approved' and "
            "{invoice.customer_id} is not null"
        )

        trigger = mapper.convert_suppress_condition(crystal_condition, "HIGH_VALUE_INVOICE")

        # Verify the trigger
        assert trigger.name == "FMT_SUPPRESS_HIGH_VALUE_INVOICE"
        assert "function FMT_SUPPRESS_HIGH_VALUE_INVOICE return boolean is" in trigger.plsql_code
        assert ":TOTAL_AMOUNT > 10000" in trigger.plsql_code
        assert ":STATUS = 'Approved'" in trigger.plsql_code
        assert ":CUSTOMER_ID IS NOT NULL" in trigger.plsql_code
        assert "exception" in trigger.plsql_code.lower()
        assert "when others then" in trigger.plsql_code.lower()

    def test_multiple_triggers(self):
        """Test generating multiple triggers."""
        mapper = ConditionMapper()

        trigger1 = mapper.convert_suppress_condition("{A} > 1", "FIELD_A")
        trigger2 = mapper.convert_suppress_condition("{B} > 2", "FIELD_B")
        trigger3 = mapper.convert_suppress_condition("{C} > 3", "FIELD_C")

        # Each should have unique name
        assert trigger1.name != trigger2.name != trigger3.name
        assert "FIELD_A" in trigger1.name
        assert "FIELD_B" in trigger2.name
        assert "FIELD_C" in trigger3.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
