#!/usr/bin/env python3
"""
Verification script to check test suite completeness.

This script analyzes the test files and reports statistics.
"""

import os
import re
from pathlib import Path


def count_tests_in_file(filepath):
    """Count test methods in a Python test file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Count test methods (def test_...)
    test_methods = re.findall(r'def test_\w+\(', content)

    # Count test classes (class Test...)
    test_classes = re.findall(r'class Test\w+[:(]', content)

    return len(test_methods), len(test_classes)


def count_lines(filepath):
    """Count lines in a file."""
    with open(filepath, 'r') as f:
        return len(f.readlines())


def main():
    """Main verification function."""
    tests_dir = Path(__file__).parent / "tests"

    print("=" * 70)
    print("RPT-to-RDF Test Suite Verification")
    print("=" * 70)
    print()

    # Find all test files
    test_files = sorted(tests_dir.glob("test_*.py"))

    total_tests = 0
    total_classes = 0
    total_lines = 0

    print(f"{'Test File':<40} {'Tests':<8} {'Classes':<8} {'Lines':<8}")
    print("-" * 70)

    for test_file in test_files:
        test_count, class_count = count_tests_in_file(test_file)
        line_count = count_lines(test_file)

        total_tests += test_count
        total_classes += class_count
        total_lines += line_count

        print(f"{test_file.name:<40} {test_count:<8} {class_count:<8} {line_count:<8}")

    print("-" * 70)
    print(f"{'TOTAL':<40} {total_tests:<8} {total_classes:<8} {total_lines:<8}")
    print()

    # Check for conftest.py
    conftest = tests_dir / "conftest.py"
    if conftest.exists():
        line_count = count_lines(conftest)
        print(f"✓ conftest.py found ({line_count} lines)")
    else:
        print("✗ conftest.py not found")

    # Check for README
    readme = tests_dir / "README.md"
    if readme.exists():
        line_count = count_lines(readme)
        print(f"✓ README.md found ({line_count} lines)")
    else:
        print("✗ README.md not found")

    # Check for pytest.ini
    pytest_ini = Path(__file__).parent / "pytest.ini"
    if pytest_ini.exists():
        line_count = count_lines(pytest_ini)
        print(f"✓ pytest.ini found ({line_count} lines)")
    else:
        print("✗ pytest.ini not found")

    # Check for run_tests.sh
    run_script = Path(__file__).parent / "run_tests.sh"
    if run_script.exists():
        line_count = count_lines(run_script)
        print(f"✓ run_tests.sh found ({line_count} lines)")
    else:
        print("✗ run_tests.sh not found")

    print()
    print("=" * 70)
    print(f"Total Test Methods: {total_tests}")
    print(f"Total Test Classes: {total_classes}")
    print(f"Total Test Code Lines: {total_lines}")
    print("=" * 70)

    # Coverage analysis
    print()
    print("Test Coverage by Component:")
    print("-" * 70)

    components = {
        "Formula Translator": "test_formula_translator.py",
        "Type Mapper": "test_type_mapper.py",
        "Layout Mapper": "test_layout_mapper.py",
        "Integration": "test_integration.py",
    }

    for component, filename in components.items():
        filepath = tests_dir / filename
        if filepath.exists():
            test_count, class_count = count_tests_in_file(filepath)
            print(f"{component:<30} {test_count:>3} tests in {class_count} classes")
        else:
            print(f"{component:<30} NOT FOUND")

    print()
    print("=" * 70)

    # Check if tests import correctly
    print()
    print("Checking test imports...")
    import_errors = []

    for test_file in test_files:
        try:
            # Try to parse the file
            with open(test_file, 'r') as f:
                content = f.read()
                compile(content, test_file.name, 'exec')
            print(f"✓ {test_file.name} - syntax OK")
        except SyntaxError as e:
            import_errors.append((test_file.name, str(e)))
            print(f"✗ {test_file.name} - syntax error: {e}")

    if import_errors:
        print()
        print("⚠ Warning: Some files have syntax errors")
        for filename, error in import_errors:
            print(f"  - {filename}: {error}")
    else:
        print()
        print("✓ All test files have valid Python syntax")

    print()
    print("=" * 70)
    print("Verification complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
