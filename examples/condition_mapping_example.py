#!/usr/bin/env python3
"""
Example: Condition Mapping in RPT-to-RDF Converter

This example demonstrates how suppress conditions and conditional formatting
are automatically converted from Crystal Reports to Oracle Reports.
"""

from src.transformation.condition_mapper import ConditionMapper, FormatTrigger
from src.parsing.report_model import Field, FormatSpec, FontSpec, Section, SectionType

def example_1_simple_suppress():
    """Example 1: Simple field suppress condition."""
    print("=" * 70)
    print("Example 1: Simple Suppress Condition")
    print("=" * 70)

    # Create a condition mapper
    mapper = ConditionMapper(trigger_prefix="FT_")

    # Crystal Reports condition: Hide amounts over 10000
    crystal_condition = "{invoice.amount} > 10000"

    # Convert to Oracle format trigger
    trigger = mapper.convert_suppress_condition(
        crystal_condition=crystal_condition,
        field_name="INVOICE_AMOUNT"
    )

    print(f"\nCrystal Condition:")
    print(f"  {crystal_condition}")
    print(f"\nOracle Format Trigger:")
    print(f"  Name: {trigger.name}")
    print(f"  Type: {trigger.trigger_type}")
    print(f"\nGenerated PL/SQL Code:")
    print(f"{trigger.plsql_code}")


def example_2_complex_condition():
    """Example 2: Complex condition with AND/OR."""
    print("\n" + "=" * 70)
    print("Example 2: Complex Condition with AND/OR")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Crystal Reports: Hide pending/processing orders over $1000
    crystal_condition = (
        "({order.status} = 'Pending' or {order.status} = 'Processing') "
        "and {order.amount} > 1000"
    )

    trigger = mapper.convert_suppress_condition(
        crystal_condition=crystal_condition,
        field_name="ORDER_STATUS"
    )

    print(f"\nCrystal Condition:")
    print(f"  {crystal_condition}")
    print(f"\nOracle Format Trigger:")
    print(f"  Name: {trigger.name}")
    print(f"\nExtracted Boolean Expression:")
    # Extract just the return statement
    for line in trigger.plsql_code.split('\n'):
        if 'return' in line and ':' in line:
            print(f"  {line.strip()}")
            break


def example_3_null_checks():
    """Example 3: NULL checks and field validation."""
    print("\n" + "=" * 70)
    print("Example 3: NULL Checks and Validation")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Crystal Reports: Show only when customer ID exists and is active
    crystal_condition = (
        "{customer.id} is not null and "
        "{customer.status} = 'Active' and "
        "{customer.balance} >= 0"
    )

    trigger = mapper.convert_suppress_condition(
        crystal_condition=crystal_condition,
        field_name="CUSTOMER_INFO"
    )

    print(f"\nCrystal Condition:")
    print(f"  {crystal_condition}")
    print(f"\nOracle Boolean Expression:")
    for line in trigger.plsql_code.split('\n'):
        if 'return' in line and ':' in line:
            print(f"  {line.strip()}")
            break


def example_4_suppress_if_zero_blank():
    """Example 4: Suppress If Zero/Blank."""
    print("\n" + "=" * 70)
    print("Example 4: Suppress If Zero and Blank")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Crystal Reports field properties
    print("\nCrystal Field Properties:")
    print("  Suppress If Zero: True")
    print("  Suppress If Blank: True")

    format_spec = FormatSpec(
        suppress_if_zero=True,
        suppress_if_blank=True
    )

    trigger = mapper.convert_suppress_if_conditions(
        format_spec=format_spec,
        field_name="AMOUNT"
    )

    print(f"\nGenerated Oracle Format Trigger:")
    print(f"  Name: {trigger.name}")
    print(f"\nBoolean Expression:")
    for line in trigger.plsql_code.split('\n'):
        if 'return' in line and ':' in line:
            print(f"  {line.strip()}")
            break


def example_5_multiple_fields():
    """Example 5: Multiple fields with different conditions."""
    print("\n" + "=" * 70)
    print("Example 5: Multiple Fields with Different Conditions")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Simulate multiple fields in a report
    fields = [
        ("AMOUNT", "{amount} > 1000"),
        ("STATUS", "{status} = 'Inactive'"),
        ("BALANCE", "{balance} <= 0"),
    ]

    print("\nGenerating format triggers for multiple fields:")

    triggers = []
    for field_name, condition in fields:
        trigger = mapper.convert_suppress_condition(condition, field_name)
        triggers.append(trigger)
        print(f"\n  Field: {field_name}")
        print(f"  Crystal: {condition}")
        print(f"  Trigger: {trigger.name}")

    print(f"\nTotal triggers generated: {len(triggers)}")


def example_6_oracle_xml_output():
    """Example 6: How it appears in Oracle XML."""
    print("\n" + "=" * 70)
    print("Example 6: Oracle Reports XML Output")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    condition = "{amount} > 5000"
    trigger = mapper.convert_suppress_condition(condition, "HIGH_AMOUNT")

    print("\nField Element in Oracle XML:")
    print(f'''
<field name="F_AMOUNT"
       source="AMOUNT"
       formatTrigger="{trigger.name}"
       x="100" y="200"
       width="150" height="20"
       fontName="Arial"
       fontSize="10"/>
    ''')

    print("\nProgram Unit in Oracle XML:")
    print(f'''
<programUnits>
  <function name="{trigger.name}" returnType="BOOLEAN">
    <textSource>{trigger.plsql_code}</textSource>
    <comment>Crystal condition: {trigger.original_condition}</comment>
  </function>
</programUnits>
    ''')


def example_7_with_functions():
    """Example 7: Conditions with functions."""
    print("\n" + "=" * 70)
    print("Example 7: Conditions with Functions")
    print("=" * 70)

    mapper = ConditionMapper(trigger_prefix="FT_")

    # Crystal Reports: Suppress if name is trimmed to empty
    crystal_condition = "trim({customer.name}) = '' or len({customer.name}) < 3"

    trigger = mapper.convert_suppress_condition(
        crystal_condition=crystal_condition,
        field_name="CUSTOMER_NAME"
    )

    print(f"\nCrystal Condition:")
    print(f"  {crystal_condition}")
    print(f"\nConverted Functions:")
    print(f"  trim() → TRIM()")
    print(f"  len() → LENGTH()")
    print(f"\nOracle Expression:")
    for line in trigger.plsql_code.split('\n'):
        if 'return' in line and ':' in line:
            print(f"  {line.strip()}")
            break


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Crystal Reports to Oracle Reports Condition Mapping Examples".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    examples = [
        example_1_simple_suppress,
        example_2_complex_condition,
        example_3_null_checks,
        example_4_suppress_if_zero_blank,
        example_5_multiple_fields,
        example_6_oracle_xml_output,
        example_7_with_functions,
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {example_func.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nFor more information, see:")
    print("  - CONDITION_MAPPING_GUIDE.md")
    print("  - CONDITION_MAPPING_QUICK_REF.md")
    print("  - IMPLEMENTATION_SUMMARY.md")
    print()


if __name__ == "__main__":
    main()
