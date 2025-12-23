# RPT-to-RDF Converter Test Suite

This directory contains comprehensive unit and integration tests for the RPT-to-RDF converter.

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── test_formula_translator.py    # Formula translation tests (80+ tests)
├── test_type_mapper.py            # Type mapping tests (70+ tests)
├── test_layout_mapper.py          # Layout mapping tests (60+ tests)
├── test_integration.py            # Integration tests (20+ tests)
├── fixtures/                      # Test fixtures and sample data
│   ├── simple/                    # Simple test cases
│   ├── medium/                    # Medium complexity test cases
│   └── complex/                   # Complex test cases
└── README.md                      # This file
```

## Running Tests

### Run All Tests
```bash
# Using the test runner script
./run_tests.sh

# Or using pytest directly
source venv/bin/activate
pytest tests/ -v
```

### Run Specific Test Files
```bash
# Formula translator tests
pytest tests/test_formula_translator.py -v

# Type mapper tests
pytest tests/test_type_mapper.py -v

# Layout mapper tests
pytest tests/test_layout_mapper.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run Tests by Category
```bash
# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration

# Run formula-related tests
pytest tests/ -v -m formula
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Test Coverage

### Formula Translator Tests (`test_formula_translator.py`)

**String Functions (8 tests)**
- LEFT, RIGHT, MID
- TRIM, LTRIM, RTRIM
- UPPER, LOWER, LENGTH
- REPLACE, REVERSE

**Date Functions (6 tests)**
- CurrentDate, CurrentDateTime, CurrentTime
- Year, Month, Day
- Hour, Minute, Second

**Numeric Functions (4 tests)**
- ABS, ROUND, TRUNCATE
- MOD, POWER, SQRT

**IIF/Conditional Tests (3 tests)**
- Simple IIF
- Nested IIF
- IIF with numeric results

**Field References (3 tests)**
- Simple field references
- Field with table prefix
- Field with spaces in name

**Formula References (3 tests)**
- @Formula syntax
- {@Formula} syntax
- Combined field and formula

**Parameter References (2 tests)**
- {?Parameter} syntax
- ?Parameter syntax

**Operators (4 tests)**
- String concatenation (&)
- Logical operators (AND, OR, NOT)
- Comparison operators

**Complex Expressions (2 tests)**
- Multi-level nested functions
- Complex calculations

**Return Types (4 tests)**
- STRING, NUMBER, DATE, DATETIME

**Oracle Name Generation (3 tests)**
- Name conversion
- Special character handling
- Names starting with digits

**Edge Cases (3 tests)**
- Empty formulas
- Whitespace-only formulas
- Comments in formulas

**Batch Operations (2 tests)**
- Empty batch
- Multiple formulas

**Column References (3 tests)**
- Single column
- Multiple columns
- No columns

**Aggregate Functions (3 tests)**
- SUM, AVG, COUNT

**Conversion Functions (2 tests)**
- ToText, ToNumber

**Error Handling (2 tests)**
- Unsupported functions
- Skip mode

**Configuration (2 tests)**
- Custom prefix
- Unsupported modes

**Total: 80+ tests**

### Type Mapper Tests (`test_type_mapper.py`)

**Basic Type Mappings (10 tests)**
- STRING → VARCHAR2
- NUMBER → NUMBER
- CURRENCY → NUMBER(15,2)
- DATE → DATE
- TIME → DATE
- DATETIME → TIMESTAMP
- BOOLEAN → VARCHAR2(1)
- MEMO → CLOB
- BLOB → BLOB
- UNKNOWN → VARCHAR2(4000)

**Type Overrides (4 tests)**
- Custom length
- Custom precision
- Custom scale
- Combined overrides

**Format String Mappings (15 tests)**
- Number formats (#,##0, #,##0.00)
- Currency formats ($#,##0.00)
- Date formats (MM/dd/yyyy, yyyy-MM-dd)
- Time formats (HH:mm:ss, h:mm tt)
- DateTime formats
- Percentage formats

**Default Values (10 tests)**
- NULL handling
- String escaping
- Number defaults
- Boolean conversion (true/false/yes/no/1/0)
- Date/Time defaults

**Conversion Functions (5 tests)**
- TO_TIMESTAMP
- TO_DATE
- No conversion needed

**PL/SQL Types (9 tests)**
- All data type conversions to PL/SQL types

**Custom Mappings (4 tests)**
- Custom type mappings
- Partial overrides

**Edge Cases (7 tests)**
- Zero length
- Large values
- Negative precision
- Special format characters

**Total: 70+ tests**

### Layout Mapper Tests (`test_layout_mapper.py`)

**Field Mapping (10 tests)**
- Simple database fields
- Formula fields
- Parameter fields
- Font styles (bold, italic, bold-italic)
- Alignments (left, center, right)
- Format strings
- Special field types

**Section Mapping (5 tests)**
- Report header/footer
- Page header/footer
- Group header/footer
- Detail sections
- Sections with fields

**Layout Mapping (6 tests)**
- Simple layouts
- Layouts with groups
- Nested groups
- All section types
- Empty layouts
- Custom page sizes

**Frame Operations (3 tests)**
- Frame creation
- Child frames
- Frame fields

**Coordinate Conversion (6 tests)**
- Twips to points
- Points to inches
- Inches to points
- CM to points
- Points to twips
- Same unit conversion

**Configuration (3 tests)**
- Custom field prefix
- Custom default font
- Coordinate unit settings

**Edge Cases (10 tests)**
- Fields with spaces
- Special characters
- Zero height sections
- Large sections
- Suppress conditions
- Frame counters
- Vertical alignment
- Table prefix removal

**Total: 60+ tests**

### Integration Tests (`test_integration.py`)

**End-to-End Transformations (4 tests)**
- Simple report
- Report with formulas
- Report with groups
- Report with all sections

**Formula and Type Integration (3 tests)**
- String formulas
- Numeric formulas with precision
- Date formulas with formatting

**Layout and Formula Integration (2 tests)**
- Formula fields in sections
- Multiple formula fields

**Error Handling (3 tests)**
- Empty formulas
- Unknown types
- Empty sections

**Complex Scenarios (3 tests)**
- Invoice report structure
- Grouped summary report
- Conditional formatting

**Total: 20+ tests**

## Test Categories

Tests are marked with the following categories:

- `unit` - Unit tests for individual components
- `integration` - Integration tests across components
- `slow` - Tests that take significant time
- `formula` - Tests related to formula translation
- `type` - Tests related to type mapping
- `layout` - Tests related to layout mapping

## Writing New Tests

### Test Naming Convention
- Test files: `test_<component>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<what_is_being_tested>`

### Example Test Structure
```python
class TestComponentName:
    """Test suite for ComponentName."""

    def setup_method(self):
        """Set up test fixtures."""
        self.component = ComponentName()

    def test_specific_feature(self):
        """Test description."""
        # Arrange
        input_data = create_test_data()

        # Act
        result = self.component.process(input_data)

        # Assert
        assert result.success
        assert result.value == expected_value
```

### Best Practices
1. Use descriptive test names
2. Include docstrings explaining what is tested
3. Follow Arrange-Act-Assert pattern
4. Test both success and failure cases
5. Use fixtures for common test data
6. Keep tests independent and isolated
7. Test edge cases and boundary conditions

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test suite should:
- Complete in under 5 minutes
- Have no external dependencies
- Be deterministic (no random failures)
- Provide clear error messages

## Coverage Goals

Target coverage levels:
- Overall: 85%+
- Formula Translator: 90%+
- Type Mapper: 90%+
- Layout Mapper: 85%+
- Integration: 80%+

## Troubleshooting

### Tests Fail to Import
```bash
# Ensure you're in the project root
cd /Users/kschweer/solutions/RPT-to-RDF

# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .
```

### Missing Dependencies
```bash
# Install test dependencies
pip install pytest pytest-cov
```

### Test Discovery Issues
```bash
# Verify pytest can find tests
pytest --collect-only
```

## Future Enhancements

Planned test additions:
- [ ] Performance benchmarks
- [ ] Stress tests with large reports
- [ ] Regression test suite
- [ ] Property-based testing with Hypothesis
- [ ] Mock external dependencies
- [ ] Parallel test execution
