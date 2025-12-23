# Changes: Conditional Formatting and Suppress Conditions

## Summary

Added comprehensive support for converting Crystal Reports suppress conditions and conditional formatting to Oracle Reports format triggers.

## New Files

### Implementation

1. **`src/transformation/condition_mapper.py`** (371 lines)
   - Core conversion logic for Crystal conditions to Oracle PL/SQL
   - `ConditionMapper` class with conversion methods
   - `FormatTrigger` dataclass for representing triggers
   - Supports field references, operators, functions, and special cases

### Tests

2. **`tests/test_condition_mapper.py`** (340 lines)
   - 27 comprehensive unit tests
   - Coverage for all conversion features
   - Integration tests for end-to-end workflows

3. **`test_manual_verification.py`** (101 lines)
   - Manual testing script (works without pytest)
   - 8 key tests with detailed output
   - Example PL/SQL code generation

### Documentation

4. **`CONDITION_MAPPING_GUIDE.md`** (500+ lines)
   - Complete guide to condition mapping
   - Architecture overview
   - Conversion examples
   - Usage instructions
   - Troubleshooting guide

5. **`CONDITION_MAPPING_QUICK_REF.md`** (200+ lines)
   - Quick reference cheat sheet
   - Conversion tables
   - Code snippets
   - Common patterns

6. **`IMPLEMENTATION_SUMMARY.md`** (300+ lines)
   - Detailed implementation summary
   - File-by-file changes
   - Technical details
   - Statistics

7. **`CHANGES.md`** (this file)
   - Summary of all changes

### Examples

8. **`examples/condition_mapping_example.py`** (250+ lines)
   - 7 comprehensive examples
   - Real-world use cases
   - XML output examples

## Modified Files

### 1. `src/transformation/transformer.py`

**Added:**
- Import for `ConditionMapper` and `FormatTrigger`
- `format_triggers` field to `TransformedReport` dataclass
- `condition_mapper` instance in `Transformer.__init__()`
- Format trigger collection in `_transform_layout()`

**Changes:**
```python
# Before
def _transform_layout(...) -> OracleLayout:
    layout = self.layout_mapper.map_layout(...)
    return layout

# After
def _transform_layout(...) -> tuple[OracleLayout, list[FormatTrigger]]:
    layout = self.layout_mapper.map_layout(..., condition_mapper=self.condition_mapper)
    format_triggers = self.layout_mapper.get_format_triggers()
    return layout, format_triggers
```

### 2. `src/transformation/layout_mapper.py`

**Added:**
- `_format_triggers` list storage
- `condition_mapper` parameter to `map_layout()`
- Format trigger generation in `_map_field()`
- `get_format_triggers()` method

**Changes:**
```python
# Before
def _map_field(self, crystal_field: Field) -> OracleField:
    ...
    return OracleField(..., visible=crystal_field.suppress_condition is None)

# After
def _map_field(self, crystal_field: Field) -> OracleField:
    ...
    # Generate format trigger if suppress condition exists
    format_trigger_name = None
    if crystal_field.suppress_condition:
        trigger = self._condition_mapper.convert_suppress_condition(...)
        self._format_triggers.append(trigger)
        format_trigger_name = trigger.name
    ...
    return OracleField(..., format_trigger=format_trigger_name)
```

### 3. `src/generation/oracle_xml_generator.py`

**Added:**
- Import for `FormatTrigger`
- `format_triggers` parameter to `_generate_program_units()`
- Format trigger function generation
- `formatTrigger` attribute to field elements

**Changes:**
```python
# Before
def _generate_program_units(self, root, formulas):
    # Only generated formula functions

def _generate_field(self, parent, field):
    # No format trigger support

# After
def _generate_program_units(self, root, formulas, format_triggers):
    # Generate both formula functions and format triggers
    for trigger in format_triggers:
        func = ET.SubElement(program_units, "function", {
            "name": trigger.name,
            "returnType": "BOOLEAN",
        })
        ...

def _generate_field(self, parent, field):
    if field.format_trigger:
        attrs["formatTrigger"] = field.format_trigger
```

## Key Features Added

### 1. Field Reference Conversion
- Crystal: `{table.field}` → Oracle: `:FIELD`
- Automatic uppercase conversion
- Table name removal

### 2. Operator Conversion
- `and` → `AND`
- `or` → `OR`
- `not` → `NOT`
- `<>` → `!=`
- `is null` → `IS NULL`
- `is not null` → `IS NOT NULL`

### 3. Function Conversion
- `trim()` → `TRIM()`
- `upper()` → `UPPER()`
- `lower()` → `LOWER()`
- `len()` → `LENGTH()`
- `isnull()` → `IS NULL`

### 4. Special Cases
- Boolean literals: `true/false` → `TRUE/FALSE`
- String concatenation: `&` → `||`
- NULL comparisons: `= null` → `IS NULL`

### 5. Built-in Suppress Conditions
- `suppress_if_zero` → `:FIELD = 0`
- `suppress_if_blank` → `:FIELD IS NULL OR TRIM(:FIELD) = ''`

### 6. Exception Handling
All format triggers include:
```plsql
exception
  when others then
    return FALSE;
end;
```

## Oracle XML Output Structure

### Before
```xml
<report>
  <data>...</data>
  <layout>
    <field name="F_AMOUNT" source="AMOUNT" visible="yes"/>
  </layout>
  <programUnits>
    <!-- Only formulas -->
  </programUnits>
</report>
```

### After
```xml
<report>
  <data>...</data>
  <layout>
    <field name="F_AMOUNT" source="AMOUNT"
           formatTrigger="FT_SUPPRESS_AMOUNT"/>
  </layout>
  <programUnits>
    <!-- Formulas -->
    <function name="CF_MyFormula" returnType="VARCHAR2">...</function>

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

## Usage Example

```python
from src.transformation.transformer import Transformer
from src.parsing.crystal_parser import CrystalParser

# Parse Crystal report
parser = CrystalParser()
report = parser.parse("report.rpt")

# Transform (condition mapping is automatic)
transformer = Transformer()
result = transformer.transform(report)

# Check format triggers
print(f"Format triggers: {len(result.format_triggers)}")
for trigger in result.format_triggers:
    print(f"  {trigger.name}: {trigger.original_condition}")

# Generate Oracle XML (includes format triggers)
from src.generation.oracle_xml_generator import OracleXMLGenerator
generator = OracleXMLGenerator()
xml = generator.generate(result)
```

## Testing

Run tests with:
```bash
# Unit tests
pytest tests/test_condition_mapper.py -v

# Manual verification
python test_manual_verification.py

# Examples
python examples/condition_mapping_example.py
```

## Statistics

- **Lines of Code Added**: ~1,800+
- **Files Created**: 8
- **Files Modified**: 3
- **Test Methods**: 27
- **Examples**: 7
- **Documentation Pages**: 4

## Breaking Changes

None. This is a new feature that extends existing functionality without breaking compatibility.

## Backward Compatibility

- Existing code continues to work
- Format triggers are optional
- Fields without suppress conditions work as before
- Empty format_triggers list if no conditions

## Known Limitations

1. **Conditional Formatting**: Oracle Reports has limited support for dynamic formatting beyond visibility
2. **Complex Functions**: Some Crystal functions may require manual conversion
3. **Section Suppression**: Field-level only for now (section-level parsed but not implemented)

## Future Enhancements

1. Section-level format triggers
2. Additional Crystal function conversions
3. Formula-based suppress conditions
4. Advanced conditional formatting
5. Performance optimizations

## Migration Notes

For existing projects:
1. No changes required to existing code
2. Suppress conditions automatically converted
3. Review generated format triggers in output XML
4. Test in Oracle Reports to verify behavior

## Related Files

See also:
- `src/parsing/report_model.py` - Field/Section models with suppress_condition
- `src/parsing/crystal_parser.py` - Extracts suppress conditions
- `src/transformation/formula_translator.py` - Formula conversion (different from conditions)

## Version Information

- **Feature Version**: 1.0
- **Implementation Date**: 2025-12-23
- **Python Version**: 3.8+
- **Dependencies**: None (uses standard library only)

## Credits

Part of the RPT-to-RDF Converter project for migrating Crystal Reports to Oracle Reports.
