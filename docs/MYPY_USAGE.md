# Using mypy for Type Checking

## Quick Start

### Run Type Checks
```bash
# From project root
./scripts/check_types.sh

# Or directly with mypy
source venv/bin/activate
mypy src/
```

## Common Commands

### Basic Type Checking
```bash
# Check all files
mypy src/

# Check specific module
mypy src/parsing/

# Check single file
mypy src/parsing/crystal_parser.py
```

### With Reports
```bash
# Generate HTML coverage report
mypy src/ --html-report .mypy_html
open .mypy_html/index.html  # macOS
xdg-open .mypy_html/index.html  # Linux

# Generate text report
mypy src/ --txt-report .mypy_txt
cat .mypy_txt/index.txt
```

### Verbose Output
```bash
# Show what mypy is doing
mypy --verbose src/

# Show error context
mypy --show-error-context src/

# Show error codes
mypy --show-error-codes src/
```

## Configuration

The project uses `mypy.ini` in the root directory. Current settings:

- **Python version**: 3.9
- **Strictness**: Progressive (can be increased)
- **Reports**: HTML and text reports enabled
- **Imports**: Follows normal imports, ignores missing third-party stubs

## Understanding Errors

### Error Format
```
src/parsing/crystal_parser.py:84: error: Incompatible return value type (got "None", expected "ReportModel")  [return-value]
```

Components:
- **File and line**: `src/parsing/crystal_parser.py:84`
- **Severity**: `error`
- **Message**: `Incompatible return value type...`
- **Error code**: `[return-value]`

### Common Errors

#### Incompatible Types
```
error: Incompatible types in assignment (expression has type "str", variable has type "int")
```
**Fix**: Ensure the assigned value matches the declared type.

#### Missing Return
```
error: Missing return statement  [return]
```
**Fix**: Add return statement or change return type to `None`.

#### Argument Type Mismatch
```
error: Argument 1 has incompatible type "str"; expected "int"
```
**Fix**: Pass the correct type or convert the value.

#### Optional Type Access
```
error: Item "None" of "Optional[str]" has no attribute "upper"
```
**Fix**: Check for None before accessing attributes:
```python
if value is not None:
    result = value.upper()
```

## Suppressing Errors

### Inline Suppression
```python
# Suppress specific error
result = some_function()  # type: ignore[error-code]

# Suppress all errors on this line
result = some_function()  # type: ignore
```

### File-Level Suppression
Add to `mypy.ini`:
```ini
[mypy-problematic_module]
ignore_errors = True
```

### Third-Party Libraries
Add to `mypy.ini`:
```ini
[mypy-library_name.*]
ignore_missing_imports = True
```

## Integration with IDEs

### VS Code
1. Install Python extension
2. Install Pylance extension
3. Settings:
   ```json
   {
     "python.linting.mypyEnabled": true,
     "python.linting.enabled": true
   }
   ```

### PyCharm
1. Settings → Tools → Python Integrated Tools
2. Enable "Type Checker: mypy"
3. Configure mypy executable path

## Continuous Integration

### GitHub Actions Example
```yaml
name: Type Check

on: [push, pull_request]

jobs:
  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mypy
      - name: Run mypy
        run: mypy src/
```

## Progressive Type Checking

Start with loose settings and gradually tighten:

### Phase 1: Current (Lenient)
```ini
disallow_untyped_defs = False
disallow_untyped_calls = False
```

### Phase 2: Moderate
```ini
disallow_untyped_defs = True  # All functions must have types
disallow_incomplete_defs = True
```

### Phase 3: Strict
```ini
disallow_untyped_calls = True
disallow_any_generics = True
strict = True  # Enable all strict flags
```

## Troubleshooting

### mypy Not Finding Imports
```bash
# Set mypy path
mypy --python-path src/ src/

# Or add to mypy.ini:
# mypy_path = src
```

### Slow Performance
```bash
# Use mypy daemon for faster checks
dmypy run -- src/

# Incremental mode (default in mypy.ini)
mypy --incremental src/
```

### Cache Issues
```bash
# Clear mypy cache
rm -rf .mypy_cache/
mypy src/
```

## Best Practices

1. **Run mypy before committing**
   ```bash
   git add .
   ./scripts/check_types.sh
   git commit -m "Your message"
   ```

2. **Add pre-commit hook**
   Create `.git/hooks/pre-commit`:
   ```bash
   #!/bin/bash
   ./scripts/check_types.sh
   ```

3. **Review HTML report regularly**
   ```bash
   mypy src/ --html-report .mypy_html
   open .mypy_html/index.html
   ```

4. **Address errors incrementally**
   - Fix one module at a time
   - Start with core modules
   - Gradually increase strictness

## Resources

- [mypy Documentation](https://mypy.readthedocs.io/)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Common Issues](https://mypy.readthedocs.io/en/stable/common_issues.html)
