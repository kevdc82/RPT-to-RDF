#!/usr/bin/env python3
"""
Manual verification script for ConditionMapper.
Tests the basic functionality without requiring pytest.
"""

from src.transformation.condition_mapper import ConditionMapper, FormatTrigger
from src.parsing.report_model import FormatSpec

def test_basic_functionality():
    """Test basic condition mapping functionality."""
    print("Testing ConditionMapper...")

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Test 1: Simple suppress condition
    print("\n1. Testing simple suppress condition...")
    condition = "{AMOUNT} > 100"
    trigger = mapper.convert_suppress_condition(condition, "AMOUNT_FIELD")
    print(f"   Trigger name: {trigger.name}")
    print(f"   Trigger type: {trigger.trigger_type}")
    print(f"   PL/SQL code:\n{trigger.plsql_code}")
    assert "FT_SUPPRESS_AMOUNT_FIELD" in trigger.name
    assert ":AMOUNT > 100" in trigger.plsql_code
    print("   ✓ PASSED")

    # Test 2: Complex condition with AND/OR
    print("\n2. Testing complex condition with AND/OR...")
    condition = "{AMOUNT} > 100 and {STATUS} = 'Active' or {TOTAL} < 50"
    trigger = mapper.convert_suppress_condition(condition)
    print(f"   PL/SQL condition: {trigger.plsql_code.split('return ')[1].split(';')[0]}")
    assert ":AMOUNT > 100 AND :STATUS = 'Active' OR :TOTAL < 50" in trigger.plsql_code
    print("   ✓ PASSED")

    # Test 3: Field references
    print("\n3. Testing field reference conversion...")
    condition = "{orders.amount} > {customers.credit_limit}"
    trigger = mapper.convert_suppress_condition(condition)
    assert ":AMOUNT" in trigger.plsql_code
    assert ":CREDIT_LIMIT" in trigger.plsql_code
    print("   ✓ PASSED - Converted to :AMOUNT and :CREDIT_LIMIT")

    # Test 4: IS NULL conversion
    print("\n4. Testing IS NULL conversion...")
    condition = "{FIELD} is null"
    trigger = mapper.convert_suppress_condition(condition)
    assert ":FIELD IS NULL" in trigger.plsql_code
    print("   ✓ PASSED")

    # Test 5: Functions
    print("\n5. Testing function conversion...")
    condition = "trim({NAME}) = 'TEST'"
    trigger = mapper.convert_suppress_condition(condition)
    assert "TRIM(:NAME)" in trigger.plsql_code
    print("   ✓ PASSED - TRIM function converted")

    # Test 6: Suppress if zero
    print("\n6. Testing suppress_if_zero...")
    format_spec = FormatSpec(suppress_if_zero=True, suppress_if_blank=False)
    trigger = mapper.convert_suppress_if_conditions(format_spec, "AMOUNT")
    assert trigger is not None
    assert ":AMOUNT = 0" in trigger.plsql_code
    print("   ✓ PASSED")

    # Test 7: Suppress if blank
    print("\n7. Testing suppress_if_blank...")
    format_spec = FormatSpec(suppress_if_zero=False, suppress_if_blank=True)
    trigger = mapper.convert_suppress_if_conditions(format_spec, "NAME")
    assert trigger is not None
    assert ":NAME IS NULL" in trigger.plsql_code
    print("   ✓ PASSED")

    # Test 8: Complex real-world example
    print("\n8. Testing complex real-world condition...")
    condition = (
        "({orders.status} = 'Pending' or {orders.status} = 'Processing') "
        "and {orders.amount} > 1000 "
        "and {customers.credit_limit} >= {orders.amount}"
    )
    trigger = mapper.convert_suppress_condition(condition, "ORDER_CHECK")
    print(f"   Generated trigger: {trigger.name}")
    assert "FT_SUPPRESS_ORDER_CHECK" in trigger.name
    assert ":STATUS = 'Pending'" in trigger.plsql_code
    assert ":AMOUNT > 1000" in trigger.plsql_code
    print("   ✓ PASSED")

    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70)

    # Print example output
    print("\nExample Format Trigger:")
    print("-" * 70)
    print(trigger.plsql_code)
    print("-" * 70)

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
