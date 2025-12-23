# Condition Mapping Guide

This guide explains how Crystal Reports suppress conditions and conditional formatting are converted to Oracle Reports format triggers.

## Overview

The RPT-to-RDF converter now supports converting Crystal Reports conditional logic to Oracle Reports format triggers. This includes:

1. **Suppress Conditions** - Formulas that control field/section visibility
2. **Conditional Formatting** - Format changes based on conditions
3. **Suppress If Zero/Blank** - Built-in suppress options

## Architecture

### Key Components

1. **`src/transformation/condition_mapper.py`** - Core conversion logic
   - `ConditionMapper` class handles all condition conversions
   - Converts Crystal syntax to PL/SQL boolean expressions
   - Generates format trigger functions

2. **`src/transformation/transformer.py`** - Integration point
   - Creates `ConditionMapper` instance
   - Passes it to `LayoutMapper`
   - Collects format triggers and adds to `TransformedReport`

3. **`src/transformation/layout_mapper.py`** - Field processing
   - Detects suppress conditions on fields
   - Calls `ConditionMapper` to generate triggers
   - Stores trigger references in `OracleField` objects

4. **`src/generation/oracle_xml_generator.py`** - XML output
   - Generates `<programUnits>` section with format trigger functions
   - Links fields to their format triggers via `formatTrigger` attribute

## Crystal Reports vs Oracle Reports

### Crystal Reports

Crystal Reports uses formulas for suppression:

```crystal
// Field suppress condition
{invoice.amount} > 10000

// Section suppress condition
{customer.region} = "WEST" and {order.status} = "Pending"

// Built-in options
Suppress If Zero: true
Suppress If Blank: true
```

### Oracle Reports

Oracle Reports uses PL/SQL format trigger functions:

```plsql
function FT_SUPPRESS_INVOICE_AMOUNT return boolean is
begin
  return :AMOUNT > 10000;
exception
  when others then
    return FALSE;
end;
```

Fields reference the trigger:

```xml
<field name="F_AMOUNT" source="AMOUNT" formatTrigger="FT_SUPPRESS_INVOICE_AMOUNT" />
```

## Conversion Examples

### Example 1: Simple Suppress Condition

**Crystal:**
```crystal
{amount} > 100
```

**Oracle PL/SQL:**
```plsql
function FT_SUPPRESS_AMOUNT return boolean is
begin
  return :AMOUNT > 100;
exception
  when others then
    return FALSE;
end;
```

### Example 2: Complex Condition with AND/OR

**Crystal:**
```crystal
({status} = "Pending" or {status} = "Processing") and {amount} > 1000
```

**Oracle PL/SQL:**
```plsql
function FT_SUPPRESS_STATUS_CHECK return boolean is
begin
  return (:STATUS = 'Pending' OR :STATUS = 'Processing') AND :AMOUNT > 1000;
exception
  when others then
    return FALSE;
end;
```

### Example 3: NULL Checks

**Crystal:**
```crystal
{customer_id} is not null and {amount} > 0
```

**Oracle PL/SQL:**
```plsql
function FT_SUPPRESS_CUSTOMER_CHECK return boolean is
begin
  return :CUSTOMER_ID IS NOT NULL AND :AMOUNT > 0;
exception
  when others then
    return FALSE;
end;
```

### Example 4: Suppress If Zero/Blank

**Crystal Field Properties:**
- Suppress If Zero: true
- Suppress If Blank: true

**Oracle PL/SQL:**
```plsql
function FT_SUPPRESS_COND_AMOUNT return boolean is
begin
  return :AMOUNT = 0 OR (:AMOUNT IS NULL OR TRIM(TO_CHAR(:AMOUNT)) = '');
exception
  when others then
    return FALSE;
end;
```

## Supported Conversions

### Operators

| Crystal | Oracle |
|---------|--------|
| `=` | `=` |
| `<>` | `!=` |
| `>` | `>` |
| `<` | `<` |
| `>=` | `>=` |
| `<=` | `<=` |
| `and` | `AND` |
| `or` | `OR` |
| `not` | `NOT` |
| `is null` | `IS NULL` |
| `is not null` | `IS NOT NULL` |

### Functions

| Crystal | Oracle |
|---------|--------|
| `trim()` | `TRIM()` |
| `upper()` | `UPPER()` |
| `lower()` | `LOWER()` |
| `len()` | `LENGTH()` |
| `isnull()` | `IS NULL` |

### Field References

- Crystal: `{table.field}` or `{field}`
- Oracle: `:FIELD` (bind variable reference)

## Generated XML Structure

The Oracle Reports XML includes format triggers in the `<programUnits>` section:

```xml
<report name="MyReport" DTDVersion="12.0.0.0">
  <data>
    <!-- data model -->
  </data>

  <layout>
    <section name="main">
      <frame name="M_BODY">
        <field name="F_AMOUNT"
               source="AMOUNT"
               formatTrigger="FT_SUPPRESS_AMOUNT"
               x="0" y="0" width="100" height="20"/>
      </frame>
    </section>
  </layout>

  <programUnits>
    <!-- Formulas -->
    <function name="CF_MyFormula" returnType="VARCHAR2">
      <textSource>...</textSource>
    </function>

    <!-- Format Triggers -->
    <function name="FT_SUPPRESS_AMOUNT" returnType="BOOLEAN">
      <textSource>function FT_SUPPRESS_AMOUNT return boolean is
begin
  return :AMOUNT > 100;
exception
  when others then
    return FALSE;
end;</textSource>
      <comment>Crystal condition: {amount} > 100</comment>
    </function>
  </programUnits>
</report>
```

## Usage

### Basic Usage

The condition mapping is automatically handled during transformation:

```python
from src.transformation.transformer import Transformer
from src.parsing.crystal_parser import CrystalParser

# Parse Crystal report
parser = CrystalParser()
report_model = parser.parse("report.rpt")

# Transform (condition mapping happens automatically)
transformer = Transformer()
transformed = transformer.transform(report_model)

# Check format triggers
print(f"Generated {len(transformed.format_triggers)} format triggers")
for trigger in transformed.format_triggers:
    print(f"  - {trigger.name}: {trigger.original_condition}")
```

### Manual Condition Conversion

You can also use `ConditionMapper` directly:

```python
from src.transformation.condition_mapper import ConditionMapper

mapper = ConditionMapper(trigger_prefix="FT_")

# Convert suppress condition
trigger = mapper.convert_suppress_condition(
    crystal_condition="{amount} > 1000",
    field_name="HIGH_VALUE"
)

print(trigger.name)        # FT_SUPPRESS_HIGH_VALUE
print(trigger.plsql_code)  # Complete PL/SQL function
```

## Limitations

1. **Conditional Formatting**: Oracle Reports format triggers primarily control visibility. Font/color changes based on conditions have limited support and may require manual implementation.

2. **Complex Functions**: Some Crystal functions may not have direct PL/SQL equivalents. The mapper will add warnings for these cases.

3. **Section Suppression**: Currently focused on field-level suppression. Section-level suppression may require additional work.

## Testing

Run the unit tests:

```bash
pytest tests/test_condition_mapper.py -v
```

Or use the manual verification script:

```bash
python test_manual_verification.py
```

## Future Enhancements

Potential improvements:

1. Support for more Crystal functions
2. Section-level format triggers
3. Advanced conditional formatting (when Oracle Reports supports it)
4. Formula-based suppress conditions
5. Parameter-based conditions

## Troubleshooting

### Common Issues

**Issue**: Generated trigger doesn't work in Oracle Reports
- **Solution**: Check that field names match exactly (case-sensitive)
- **Solution**: Verify data types are compatible with operators used

**Issue**: Condition is too complex
- **Solution**: Break into multiple simpler conditions
- **Solution**: Use formulas in Crystal, then convert formulas separately

**Issue**: Function not supported
- **Solution**: Check warnings in `trigger.warnings`
- **Solution**: Manually implement the function in PL/SQL

## Additional Resources

- Oracle Reports Builder Documentation
- Crystal Reports Formula Workshop Guide
- PL/SQL Language Reference
- RPT-to-RDF Converter Main Documentation
