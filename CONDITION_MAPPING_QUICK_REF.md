# Condition Mapping Quick Reference

## Crystal → Oracle Conversion Cheat Sheet

### Field References
```
Crystal:  {table.field}  or  {field}
Oracle:   :FIELD
```

### Operators
```
Crystal     Oracle
=           =
<>          !=
>           >
<           <
>=          >=
<=          <=
and         AND
or          OR
not         NOT
is null     IS NULL
```

### Common Functions
```
Crystal         Oracle
trim(x)         TRIM(x)
upper(x)        UPPER(x)
lower(x)        LOWER(x)
len(x)          LENGTH(x)
isnull(x)       x IS NULL
```

### String Operations
```
Crystal:  {FirstName} & " " & {LastName}
Oracle:   :FIRSTNAME || ' ' || :LASTNAME
```

## Code Examples

### Simple Condition
```crystal
// Crystal
{amount} > 100
```
```plsql
-- Oracle
function FT_SUPPRESS_AMOUNT return boolean is
begin
  return :AMOUNT > 100;
exception
  when others then
    return FALSE;
end;
```

### Complex AND/OR
```crystal
// Crystal
({status} = "Pending" or {status} = "Processing") and {amount} > 1000
```
```plsql
-- Oracle
return (:STATUS = 'Pending' OR :STATUS = 'Processing') AND :AMOUNT > 1000;
```

### NULL Check
```crystal
// Crystal
{customer_id} is not null
```
```plsql
-- Oracle
return :CUSTOMER_ID IS NOT NULL;
```

### Suppress If Zero
```crystal
// Crystal Field Property
Suppress If Zero: true
```
```plsql
-- Oracle
return :AMOUNT = 0;
```

### Suppress If Blank
```crystal
// Crystal Field Property
Suppress If Blank: true
```
```plsql
-- Oracle
return (:NAME IS NULL OR TRIM(TO_CHAR(:NAME)) = '');
```

## Quick API Reference

### ConditionMapper Class

```python
from src.transformation.condition_mapper import ConditionMapper

mapper = ConditionMapper(trigger_prefix="FT_")

# Convert suppress condition
trigger = mapper.convert_suppress_condition(
    crystal_condition="{amount} > 1000",
    field_name="AMOUNT_FIELD"
)

# Convert suppress_if_zero/blank
from src.parsing.report_model import FormatSpec
format_spec = FormatSpec(suppress_if_zero=True)
trigger = mapper.convert_suppress_if_conditions(
    format_spec=format_spec,
    field_name="AMOUNT"
)
```

### FormatTrigger Object

```python
trigger.name              # "FT_SUPPRESS_AMOUNT_FIELD"
trigger.plsql_code        # Complete PL/SQL function
trigger.trigger_type      # "suppress" or "conditional_format"
trigger.original_condition # Original Crystal condition
trigger.warnings          # List of conversion warnings
```

## Oracle XML Output

```xml
<!-- Field with format trigger -->
<field name="F_AMOUNT"
       source="AMOUNT"
       formatTrigger="FT_SUPPRESS_AMOUNT"
       x="0" y="0" width="100" height="20"/>

<!-- Program unit definition -->
<programUnits>
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
```

## Testing

```bash
# Run unit tests
pytest tests/test_condition_mapper.py -v

# Manual verification
python test_manual_verification.py
```

## Common Patterns

### Range Check
```crystal
{value} >= 0 and {value} <= 100
```
```plsql
:VALUE >= 0 AND :VALUE <= 100
```

### Multiple OR Conditions
```crystal
{status} = "A" or {status} = "B" or {status} = "C"
```
```plsql
:STATUS = 'A' OR :STATUS = 'B' OR :STATUS = 'C'
```

### Not NULL with Value Check
```crystal
{field} is not null and {field} <> ""
```
```plsql
:FIELD IS NOT NULL AND :FIELD != ''
```

### Combined Zero and Null
```crystal
{amount} <> 0 and {amount} is not null
```
```plsql
:AMOUNT != 0 AND :AMOUNT IS NOT NULL
```

## Best Practices

1. **Keep conditions simple** - Complex conditions are harder to debug
2. **Test in Oracle Reports** - Verify triggers work as expected
3. **Check warnings** - Review `trigger.warnings` for potential issues
4. **Use bind variables** - Always prefix with `:` in PL/SQL
5. **Handle exceptions** - All triggers include exception handling
6. **Document complex logic** - Add comments for business rules

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Field name mismatch | Check case - Oracle uses UPPERCASE |
| Trigger not firing | Verify field name matches source exactly |
| Syntax error in PL/SQL | Check for unsupported Crystal functions |
| Unexpected behavior | Review conversion warnings |
| NULL comparison fails | Use `IS NULL` not `= NULL` |

## File Locations

```
src/transformation/condition_mapper.py   # Implementation
tests/test_condition_mapper.py           # Unit tests
test_manual_verification.py              # Manual testing
CONDITION_MAPPING_GUIDE.md               # Full documentation
```
