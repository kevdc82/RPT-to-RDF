# Crystal Reports to Oracle PL/SQL Formula Reference

## Complete Function Mapping Guide

This document provides a comprehensive reference for all supported Crystal Reports formula functions and their Oracle PL/SQL equivalents.

---

## String Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `Left(str, n)` | `SUBSTR(str, 1, n)` | Get leftmost n characters | `Left({Name}, 5)` → `SUBSTR(:NAME, 1, 5)` |
| `Right(str, n)` | `SUBSTR(str, -1 * n)` | Get rightmost n characters | `Right({Name}, 3)` → `SUBSTR(:NAME, -1 * 3)` |
| `Mid(str, start, len)` | `SUBSTR(str, start, len)` | Get substring | `Mid({Name}, 2, 5)` → `SUBSTR(:NAME, 2, 5)` |
| `Trim(str)` | `TRIM(str)` | Remove leading/trailing spaces | `Trim({Name})` → `TRIM(:NAME)` |
| `LTrim(str)` | `LTRIM(str)` | Remove leading spaces | `LTrim({Name})` → `LTRIM(:NAME)` |
| `RTrim(str)` | `RTRIM(str)` | Remove trailing spaces | `RTrim({Name})` → `RTRIM(:NAME)` |
| `Upper(str)` | `UPPER(str)` | Convert to uppercase | `Upper({Name})` → `UPPER(:NAME)` |
| `UCase(str)` | `UPPER(str)` | Convert to uppercase (alias) | `UCase({Name})` → `UPPER(:NAME)` |
| `Lower(str)` | `LOWER(str)` | Convert to lowercase | `Lower({Name})` → `LOWER(:NAME)` |
| `LCase(str)` | `LOWER(str)` | Convert to lowercase (alias) | `LCase({Name})` → `LOWER(:NAME)` |
| `ProperCase(str)` | `INITCAP(str)` | Convert to proper case | `ProperCase({Name})` → `INITCAP(:NAME)` |
| `Length(str)` | `LENGTH(str)` | Get string length | `Length({Name})` → `LENGTH(:NAME)` |
| `Len(str)` | `LENGTH(str)` | Get string length (alias) | `Len({Name})` → `LENGTH(:NAME)` |
| `InStr(str, search)` | `INSTR(str, search)` | Find substring position | `InStr({Name}, 'A')` → `INSTR(:NAME, 'A')` |
| `InStrRev(str, search)` | `INSTR(str, search, -1)` | Find substring from end | `InStrRev({Name}, 'A')` → `INSTR(:NAME, 'A', -1)` |
| `Replace(str, old, new)` | `REPLACE(str, old, new)` | Replace substring | `Replace({Name}, 'A', 'B')` → `REPLACE(:NAME, 'A', 'B')` |
| `Space(n)` | `RPAD(' ', n)` | Generate n spaces | `Space(10)` → `RPAD(' ', 10)` |
| `Replicate(str, n)` | `RPAD(str, LENGTH(str) * n, str)` | Repeat string n times | `Replicate('AB', 3)` → `RPAD('AB', LENGTH('AB') * 3, 'AB')` |
| `ReplicateString(str, n)` | `RPAD(str, LENGTH(str) * n, str)` | Repeat string n times | `ReplicateString('AB', 3)` → `RPAD('AB', LENGTH('AB') * 3, 'AB')` |
| `Chr(n)` | `CHR(n)` | Convert ASCII to character | `Chr(65)` → `CHR(65)` (returns 'A') |
| `Asc(str)` | `ASCII(str)` | Get ASCII code | `Asc('A')` → `ASCII('A')` (returns 65) |
| `StrReverse(str)` | `REVERSE(str)` | Reverse string | `StrReverse('ABC')` → `REVERSE('ABC')` (returns 'CBA') |
| `StrCmp(s1, s2)` | `CASE WHEN...` | Compare strings | `StrCmp('a', 'b')` → `CASE WHEN 'a' < 'b' THEN -1 WHEN 'a' > 'b' THEN 1 ELSE 0 END` |
| `Val(str)` | `TO_NUMBER(str)` | Convert to number | `Val('123')` → `TO_NUMBER('123')` |
| `Str(num)` | `TO_CHAR(num)` | Convert to string | `Str(123)` → `TO_CHAR(123)` |

---

## Date & Time Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `CurrentDate` | `TRUNC(SYSDATE)` | Current date (no time) | `CurrentDate` → `TRUNC(SYSDATE)` |
| `CurrentDateTime` | `SYSTIMESTAMP` | Current date and time | `CurrentDateTime` → `SYSTIMESTAMP` |
| `CurrentTime` | `TO_CHAR(SYSDATE, 'HH24:MI:SS')` | Current time | `CurrentTime` → `TO_CHAR(SYSDATE, 'HH24:MI:SS')` |
| `Now` | `SYSDATE` | Current date/time | `Now` → `SYSDATE` |
| `Today` | `TRUNC(SYSDATE)` | Today's date | `Today` → `TRUNC(SYSDATE)` |
| `Timer` | `(SYSDATE - TRUNC(SYSDATE)) * 86400` | Seconds since midnight | `Timer` → `(SYSDATE - TRUNC(SYSDATE)) * 86400` |
| `Date(datetime)` | `TRUNC(datetime)` | Extract date part | `Date({OrderDate})` → `TRUNC(:ORDERDATE)` |
| `Year(date)` | `EXTRACT(YEAR FROM date)` | Extract year | `Year({OrderDate})` → `EXTRACT(YEAR FROM :ORDERDATE)` |
| `Month(date)` | `EXTRACT(MONTH FROM date)` | Extract month | `Month({OrderDate})` → `EXTRACT(MONTH FROM :ORDERDATE)` |
| `Day(date)` | `EXTRACT(DAY FROM date)` | Extract day | `Day({OrderDate})` → `EXTRACT(DAY FROM :ORDERDATE)` |
| `Hour(datetime)` | `EXTRACT(HOUR FROM CAST(datetime AS TIMESTAMP))` | Extract hour | `Hour({OrderTime})` → `EXTRACT(HOUR FROM CAST(:ORDERTIME AS TIMESTAMP))` |
| `Minute(datetime)` | `EXTRACT(MINUTE FROM CAST(datetime AS TIMESTAMP))` | Extract minute | `Minute({OrderTime})` → `EXTRACT(MINUTE FROM CAST(:ORDERTIME AS TIMESTAMP))` |
| `Second(datetime)` | `EXTRACT(SECOND FROM CAST(datetime AS TIMESTAMP))` | Extract second | `Second({OrderTime})` → `EXTRACT(SECOND FROM CAST(:ORDERTIME AS TIMESTAMP))` |
| `DayOfWeek(date)` | `TO_NUMBER(TO_CHAR(date, 'D'))` | Day of week (1-7) | `DayOfWeek({OrderDate})` → `TO_NUMBER(TO_CHAR(:ORDERDATE, 'D'))` |
| `WeekDay(date)` | `TO_CHAR(date, 'D')` | Day of week string | `WeekDay({OrderDate})` → `TO_CHAR(:ORDERDATE, 'D')` |
| `MonthName(date)` | `TO_CHAR(date, 'Month')` | Month name | `MonthName({OrderDate})` → `TO_CHAR(:ORDERDATE, 'Month')` |
| `DateSerial(y, m, d)` | `TO_DATE(y||'-'||m||'-'||d, 'YYYY-MM-DD')` | Create date | `DateSerial(2024, 1, 15)` → `TO_DATE(2024||'-'||1||'-'||15, 'YYYY-MM-DD')` |
| `DateValue(str)` | `TO_DATE(str, 'YYYY-MM-DD')` | Parse date | `DateValue('2024-01-15')` → `TO_DATE('2024-01-15', 'YYYY-MM-DD')` |
| `TimeValue(str)` | `TO_DATE(str, 'HH24:MI:SS')` | Parse time | `TimeValue('14:30:00')` → `TO_DATE('14:30:00', 'HH24:MI:SS')` |

### DatePart Function

The `DatePart` function extracts different parts of a date based on the interval specified:

| Interval | Oracle Equivalent | Description | Example |
|----------|-------------------|-------------|---------|
| `'yyyy'`, `'year'` | `EXTRACT(YEAR FROM date)` | Year | `DatePart('yyyy', {Date})` → `EXTRACT(YEAR FROM :DATE)` |
| `'q'`, `'quarter'` | `TO_CHAR(date, 'Q')` | Quarter (1-4) | `DatePart('q', {Date})` → `TO_CHAR(:DATE, 'Q')` |
| `'m'`, `'month'` | `EXTRACT(MONTH FROM date)` | Month (1-12) | `DatePart('m', {Date})` → `EXTRACT(MONTH FROM :DATE)` |
| `'d'`, `'day'` | `EXTRACT(DAY FROM date)` | Day of month | `DatePart('d', {Date})` → `EXTRACT(DAY FROM :DATE)` |
| `'y'`, `'dayofyear'` | `TO_CHAR(date, 'DDD')` | Day of year (1-366) | `DatePart('y', {Date})` → `TO_CHAR(:DATE, 'DDD')` |
| `'w'`, `'ww'`, `'week'` | `TO_CHAR(date, 'IW')` | Week number | `DatePart('w', {Date})` → `TO_CHAR(:DATE, 'IW')` |
| `'weekday'` | `TO_CHAR(date, 'D')` | Day of week | `DatePart('weekday', {Date})` → `TO_CHAR(:DATE, 'D')` |
| `'h'`, `'hour'` | `EXTRACT(HOUR FROM CAST(date AS TIMESTAMP))` | Hour | `DatePart('h', {DateTime})` → `EXTRACT(HOUR FROM CAST(:DATETIME AS TIMESTAMP))` |
| `'n'`, `'minute'` | `EXTRACT(MINUTE FROM CAST(date AS TIMESTAMP))` | Minute | `DatePart('n', {DateTime})` → `EXTRACT(MINUTE FROM CAST(:DATETIME AS TIMESTAMP))` |
| `'s'`, `'second'` | `EXTRACT(SECOND FROM CAST(date AS TIMESTAMP))` | Second | `DatePart('s', {DateTime})` → `EXTRACT(SECOND FROM CAST(:DATETIME AS TIMESTAMP))` |

---

## Numeric Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `Abs(n)` | `ABS(n)` | Absolute value | `Abs(-5)` → `ABS(-5)` |
| `Round(n, places)` | `ROUND(n, places)` | Round to decimals | `Round(3.14159, 2)` → `ROUND(3.14159, 2)` |
| `Truncate(n, places)` | `TRUNC(n, places)` | Truncate decimals | `Truncate(3.14159, 2)` → `TRUNC(3.14159, 2)` |
| `Int(n)` | `FLOOR(n)` | Round down to integer | `Int(3.7)` → `FLOOR(3.7)` |
| `Fix(n)` | `TRUNC(n)` | Truncate to integer | `Fix(3.7)` → `TRUNC(3.7)` |
| `Ceiling(n)` | `CEIL(n)` | Round up to integer | `Ceiling(3.2)` → `CEIL(3.2)` |
| `Floor(n)` | `FLOOR(n)` | Round down to integer | `Floor(3.7)` → `FLOOR(3.7)` |
| `Mod(n, divisor)` | `MOD(n, divisor)` | Modulo (remainder) | `Mod(10, 3)` → `MOD(10, 3)` |
| `Remainder(n, divisor)` | `REMAINDER(n, divisor)` | IEEE remainder | `Remainder(10, 3)` → `REMAINDER(10, 3)` |
| `Sgn(n)` | `SIGN(n)` | Sign of number | `Sgn(-5)` → `SIGN(-5)` (returns -1) |
| `Sign(n)` | `SIGN(n)` | Sign of number | `Sign(5)` → `SIGN(5)` (returns 1) |
| `Sqrt(n)` | `SQRT(n)` | Square root | `Sqrt(16)` → `SQRT(16)` |
| `Sqr(n)` | `SQRT(n)` | Square root (alias) | `Sqr(16)` → `SQRT(16)` |
| `Exp(n)` | `EXP(n)` | e raised to power n | `Exp(2)` → `EXP(2)` |
| `Log(n)` | `LN(n)` | Natural logarithm | `Log(10)` → `LN(10)` |
| `Log10(n)` | `LOG(10, n)` | Base-10 logarithm | `Log10(100)` → `LOG(10, 100)` |
| `Power(base, exp)` | `POWER(base, exp)` | Raise to power | `Power(2, 3)` → `POWER(2, 3)` |

---

## Trigonometric Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `Sin(n)` | `SIN(n)` | Sine | `Sin(1.57)` → `SIN(1.57)` |
| `Cos(n)` | `COS(n)` | Cosine | `Cos(0)` → `COS(0)` |
| `Tan(n)` | `TAN(n)` | Tangent | `Tan(0.785)` → `TAN(0.785)` |
| `Asin(n)` | `ASIN(n)` | Arcsine | `Asin(0.5)` → `ASIN(0.5)` |
| `Acos(n)` | `ACOS(n)` | Arccosine | `Acos(0.5)` → `ACOS(0.5)` |
| `Atan(n)` | `ATAN(n)` | Arctangent | `Atan(1)` → `ATAN(1)` |
| `Atn(n)` | `ATAN(n)` | Arctangent (alias) | `Atn(1)` → `ATAN(1)` |

---

## Conversion Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `ToText(value)` | `TO_CHAR(value)` | Convert to text | `ToText(123)` → `TO_CHAR(123)` |
| `ToNumber(str)` | `TO_NUMBER(str)` | Convert to number | `ToNumber('123')` → `TO_NUMBER('123')` |
| `CStr(value)` | `TO_CHAR(value)` | Convert to string | `CStr(123)` → `TO_CHAR(123)` |
| `CDbl(str)` | `TO_NUMBER(str)` | Convert to double | `CDbl('123.45')` → `TO_NUMBER('123.45')` |
| `CDate(str)` | `TO_DATE(str)` | Convert to date | `CDate('2024-01-15')` → `TO_DATE('2024-01-15')` |
| `CBool(value)` | `CASE WHEN value THEN 'Y' ELSE 'N' END` | Convert to boolean | `CBool({Flag})` → `CASE WHEN :FLAG THEN 'Y' ELSE 'N' END` |

---

## Aggregate Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `Sum(field)` | `SUM(field)` | Sum of values | `Sum({Amount})` → `SUM(:AMOUNT)` |
| `Avg(field)` | `AVG(field)` | Average of values | `Avg({Amount})` → `AVG(:AMOUNT)` |
| `Average(field)` | `AVG(field)` | Average of values (alias) | `Average({Amount})` → `AVG(:AMOUNT)` |
| `Count(field)` | `COUNT(field)` | Count of values | `Count({OrderID})` → `COUNT(:ORDERID)` |
| `Max(field)` | `MAX(field)` | Maximum value | `Max({Amount})` → `MAX(:AMOUNT)` |
| `Maximum(field)` | `MAX(field)` | Maximum value (alias) | `Maximum({Amount})` → `MAX(:AMOUNT)` |
| `Min(field)` | `MIN(field)` | Minimum value | `Min({Amount})` → `MIN(:AMOUNT)` |
| `Minimum(field)` | `MIN(field)` | Minimum value (alias) | `Minimum({Amount})` → `MIN(:AMOUNT)` |
| `DistinctCount(field)` | `COUNT(DISTINCT field)` | Count of distinct values | `DistinctCount({Category})` → `COUNT(DISTINCT :CATEGORY)` |

---

## Running Totals

| Crystal Function | Oracle Equivalent | Description | Notes |
|-----------------|-------------------|-------------|-------|
| `RunningTotal(field)` | `SUM(field) OVER (ORDER BY ROWNUM)` | Cumulative sum | Requires manual specification of ORDER BY clause |

**Example:**
```crystal
RunningTotal({Amount})
```
Translates to:
```sql
SUM(:AMOUNT) OVER (ORDER BY ROWNUM)
```

**Note:** You should replace `ROWNUM` with an appropriate ORDER BY column for your use case.

---

## Logical Functions

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `IIF(cond, true_val, false_val)` | `CASE WHEN cond THEN true_val ELSE false_val END` | Conditional expression | See below |
| `IsNull(field)` | `(field IS NULL)` | Check if null | `IsNull({Field})` → `(:FIELD IS NULL)` |
| `IsNothing(field)` | `(field IS NULL)` | Check if null | `IsNothing({Field})` → `(:FIELD IS NULL)` |

### IIF Examples

**Simple IIF:**
```crystal
IIF({Amount} > 100, 'High', 'Low')
```
Translates to:
```sql
CASE WHEN :AMOUNT > 100 THEN 'High' ELSE 'Low' END
```

**Nested IIF:**
```crystal
IIF({Amount} > 1000, 'Very High', IIF({Amount} > 100, 'High', 'Low'))
```
Translates to:
```sql
CASE WHEN :AMOUNT > 1000 THEN 'Very High'
ELSE CASE WHEN :AMOUNT > 100 THEN 'High' ELSE 'Low' END END
```

**Complex Nested IIF:**
```crystal
IIF({Score} >= 90, 'A', IIF({Score} >= 80, 'B', IIF({Score} >= 70, 'C', 'F')))
```
Translates to:
```sql
CASE WHEN :SCORE >= 90 THEN 'A'
ELSE CASE WHEN :SCORE >= 80 THEN 'B'
ELSE CASE WHEN :SCORE >= 70 THEN 'C' ELSE 'F' END END END
```

---

## Null Handling

| Crystal Function | Oracle Equivalent | Description | Example |
|-----------------|-------------------|-------------|---------|
| `NV(value, default)` | `NVL(value, default)` | Null value replacement | `NV({Field}, 0)` → `NVL(:FIELD, 0)` |

---

## Operators

| Crystal Operator | Oracle Operator | Description | Example |
|-----------------|-----------------|-------------|---------|
| `&` | `\|\|` | String concatenation | `{First} & ' ' & {Last}` → `:FIRST \|\| ' ' \|\| :LAST` |
| `And` | `AND` | Logical AND | `{A} And {B}` → `:A AND :B` |
| `Or` | `OR` | Logical OR | `{A} Or {B}` → `:A OR :B` |
| `Not` | `NOT` | Logical NOT | `Not {Flag}` → `NOT :FLAG` |
| `<>` | `!=` | Not equal | `{A} <> {B}` → `:A != :B` |
| `=` | `=` | Equal | `{A} = {B}` → `:A = :B` |
| `Mod` | `MOD` | Modulo operator | `{A} Mod {B}` → `MOD(:A, :B)` |

---

## Field References

| Crystal Syntax | Oracle Syntax | Description |
|---------------|---------------|-------------|
| `{FieldName}` | `:FIELDNAME` | Simple field reference |
| `{Table.FieldName}` | `:FIELDNAME` | Table-qualified field |
| `{Field Name With Spaces}` | `:FIELD_NAME_WITH_SPACES` | Field with spaces |

---

## Formula References

| Crystal Syntax | Oracle Syntax | Description |
|---------------|---------------|-------------|
| `@FormulaName` | `CF_FORMULANAME()` | Formula reference |
| `{@FormulaName}` | `CF_FORMULANAME()` | Formula reference in braces |

---

## Parameter References

| Crystal Syntax | Oracle Syntax | Description |
|---------------|---------------|-------------|
| `?ParamName` | `:P_PARAMNAME` | Parameter reference |
| `{?ParamName}` | `:P_PARAMNAME` | Parameter reference in braces |

---

## Complex Examples

### Example 1: Full Name Construction
```crystal
ProperCase(Trim({FirstName})) & ' ' & ProperCase(Trim({LastName}))
```
Translates to:
```sql
INITCAP(TRIM(:FIRSTNAME)) || ' ' || INITCAP(TRIM(:LASTNAME))
```

### Example 2: Age Calculation
```crystal
DatePart('yyyy', CurrentDate) - DatePart('yyyy', {BirthDate})
```
Translates to:
```sql
EXTRACT(YEAR FROM TRUNC(SYSDATE)) - EXTRACT(YEAR FROM :BIRTHDATE)
```

### Example 3: Revenue Category
```crystal
IIF({Revenue} > 1000000, 'Enterprise',
    IIF({Revenue} > 100000, 'Corporate',
        IIF({Revenue} > 10000, 'Small Business', 'Startup')))
```
Translates to:
```sql
CASE WHEN :REVENUE > 1000000 THEN 'Enterprise'
ELSE CASE WHEN :REVENUE > 100000 THEN 'Corporate'
ELSE CASE WHEN :REVENUE > 10000 THEN 'Small Business'
ELSE 'Startup' END END END
```

### Example 4: Formatted Phone Number
```crystal
'(' & Left({Phone}, 3) & ') ' & Mid({Phone}, 4, 3) & '-' & Right({Phone}, 4)
```
Translates to:
```sql
'(' || SUBSTR(:PHONE, 1, 3) || ') ' || SUBSTR(:PHONE, 4, 3) || '-' || SUBSTR(:PHONE, -1 * 4)
```

### Example 5: Running Total with Custom Order
```crystal
RunningTotal({SalesAmount})
```
Translates to (manual adjustment needed):
```sql
SUM(:SALESAMOUNT) OVER (ORDER BY :ORDERDATE, :ORDERID)
```

---

## Notes

1. **Case Sensitivity**: Crystal function names are case-insensitive; the translator handles this automatically.

2. **Field References**: Always converted to uppercase with underscores replacing spaces.

3. **Formula Prefix**: By default, Crystal formulas are prefixed with `CF_` in Oracle (configurable).

4. **Parameter Prefix**: Parameters are prefixed with `P_` in Oracle.

5. **Return Types**: The translator automatically determines Oracle return types:
   - `DataType.STRING` → `VARCHAR2`
   - `DataType.NUMBER` → `NUMBER`
   - `DataType.DATE` → `DATE`
   - `DataType.DATETIME` → `TIMESTAMP`
   - `DataType.BOOLEAN` → `VARCHAR2`

6. **Warnings**: Some functions generate warnings for manual review:
   - `RunningTotal`: Requires ORDER BY clause customization
   - `DatePart`: Unknown intervals
   - Unknown functions: Passed through with warning

---

## Unsupported Functions

The following Crystal functions require manual conversion:
- `WhilePrintingRecords`
- `WhileReadingRecords`
- `EvaluateAfter`
- `SharedVariable` / `Shared`
- `Previous` / `Next`
- `DrillDownGroupLevel`
- `GroupSelection`
- `RecordSelection`
- `Switch` (special handling required)
- `Choose` (special handling required)

---

## Version History

- **v1.1** (2025-12-23): Added DatePart, Timer, RunningTotal, and 20+ new function mappings
- **v1.0** (Initial): Basic formula translation support

---

## Support

For issues or questions about formula translation, refer to:
- Main project documentation
- Unit tests in `tests/test_formula_translator.py`
- Configuration file `config/formula_mappings.yaml`
