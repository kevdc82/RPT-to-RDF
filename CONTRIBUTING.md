# Contributing to RPT-to-RDF

Thank you for your interest in contributing to the Crystal Reports to Oracle Reports converter!

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kevdc82/RPT-to-RDF.git
   cd RPT-to-RDF
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install dev dependencies
   ```

4. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting (line length: 100)
- **isort** - Import sorting (profile: black)
- **flake8** - Linting
- **mypy** - Type checking

### Running Code Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_formula_translator.py -v

# Run specific test
pytest tests/test_formula_translator.py::TestFormulaTranslator::test_left_function -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test classes `Test*`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested

Example:
```python
def test_left_function_converts_to_substr():
    """Test that Crystal Left() converts to Oracle SUBSTR()."""
    translator = FormulaTranslator()
    result = translator.translate_expression("Left(name, 5)")
    assert "SUBSTR" in result.oracle_expression
```

## Pull Request Process

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write code following the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run checks:**
   ```bash
   # Run all checks
   black --check src/ tests/
   isort --check-only src/ tests/
   flake8 src/ tests/
   pytest tests/ -v
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. **Push and create a Pull Request:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements:**
   - All CI checks must pass
   - Tests must cover new functionality
   - Documentation must be updated
   - At least one approval required

## Project Structure

```
rpt-to-rdf/
├── src/
│   ├── extraction/      # RPT file extraction
│   ├── parsing/         # Crystal XML parsing
│   ├── transformation/  # Crystal to Oracle conversion
│   ├── generation/      # Oracle XML/RDF generation
│   └── utils/           # Utilities and helpers
├── tests/               # Test files
├── config/              # Configuration files
├── tools/               # External tools (RptToXml)
└── docs/                # Documentation
```

## Error Codes

When adding new error conditions, use the standardized error code format:

- `RPT-1xxx`: Extraction errors
- `RPT-2xxx`: Parsing errors
- `RPT-3xxx`: Formula errors
- `RPT-4xxx`: Type errors
- `RPT-5xxx`: Layout errors
- `RPT-6xxx`: Connection errors
- `RPT-7xxx`: Subreport errors
- `RPT-8xxx`: Generation errors
- `RPT-9xxx`: General/Configuration errors

Add new error codes to `src/utils/error_handler.py` with descriptions and suggestions.

## Adding New Formula Mappings

To add support for a new Crystal Reports function:

1. Add the mapping to `FUNCTION_MAP` in `src/transformation/formula_translator.py`
2. Add a test case in `tests/test_formula_translator.py`
3. Document the mapping in the README if it's commonly used

Example:
```python
# In formula_translator.py
FUNCTION_MAP = {
    # ... existing mappings
    "MyFunction": "ORACLE_EQUIVALENT({0}, {1})",
}
```

## Reporting Issues

When reporting issues, please include:

1. Python version
2. Operating system
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Error messages (including error codes)
7. Sample RPT file (if possible)

## Questions?

If you have questions about contributing, please open an issue or reach out to the maintainers.
