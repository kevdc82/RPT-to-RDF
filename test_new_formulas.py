#!/usr/bin/env python3
"""Quick test script to verify new formula translations."""

import sys
sys.path.insert(0, '/Users/kschweer/solutions/RPT-to-RDF')

from src.parsing.report_model import Formula, DataType, FormulaSyntax
from src.transformation.formula_translator import FormulaTranslator


def test_new_functions():
    """Test all the new formula functions."""
    translator = FormulaTranslator(formula_prefix="CF_")

    print("Testing new formula translations...")
    print("=" * 60)

    tests = [
        # String functions
        ("Chr", "Chr(65)", DataType.STRING, "CHR(65)"),
        ("Asc", "Asc('A')", DataType.NUMBER, "ASCII('A')"),
        ("StrCmp", "StrCmp('abc', 'def')", DataType.NUMBER, "CASE WHEN"),
        ("ReplicateString", "ReplicateString('AB', 5)", DataType.STRING, "RPAD"),
        ("StrReverse", "StrReverse('hello')", DataType.STRING, "REVERSE"),
        ("ProperCase", "ProperCase('hello world')", DataType.STRING, "INITCAP"),

        # Date functions
        ("WeekDay", "WeekDay({DateField})", DataType.STRING, "TO_CHAR"),
        ("MonthName", "MonthName({DateField})", DataType.STRING, "Month"),
        ("Timer", "Timer", DataType.NUMBER, "86400"),
        ("DatePart_Year", "DatePart('yyyy', {DateField})", DataType.NUMBER, "EXTRACT(YEAR"),
        ("DatePart_Quarter", "DatePart('q', {DateField})", DataType.NUMBER, "TO_CHAR"),

        # Math functions
        ("Sqr", "Sqr(16)", DataType.NUMBER, "SQRT(16)"),
        ("Exp", "Exp(2)", DataType.NUMBER, "EXP(2)"),
        ("Log", "Log(10)", DataType.NUMBER, "LN(10)"),
        ("Sgn", "Sgn(-5)", DataType.NUMBER, "SIGN(-5)"),
        ("Fix", "Fix(3.7)", DataType.NUMBER, "TRUNC(3.7)"),
        ("Int", "Int(3.7)", DataType.NUMBER, "FLOOR(3.7)"),
        ("Ceiling", "Ceiling(3.2)", DataType.NUMBER, "CEIL(3.2)"),

        # Aggregate functions
        ("Average", "Average({Amount})", DataType.NUMBER, "AVG(:AMOUNT)"),
        ("Maximum", "Maximum({Amount})", DataType.NUMBER, "MAX(:AMOUNT)"),
        ("Minimum", "Minimum({Amount})", DataType.NUMBER, "MIN(:AMOUNT)"),

        # Running totals
        ("RunningTotal", "RunningTotal({Amount})", DataType.NUMBER, "SUM(:AMOUNT) OVER"),

        # Nested IIF
        ("NestedIIF", "IIF({A} > 1, 'X', IIF({B} > 2, 'Y', 'Z'))", DataType.STRING, "CASE WHEN"),
    ]

    passed = 0
    failed = 0

    for name, expression, return_type, expected_substring in tests:
        try:
            formula = Formula(
                name=f"Test{name}",
                expression=expression,
                return_type=return_type,
                syntax=FormulaSyntax.CRYSTAL,
            )
            result = translator.translate(formula)

            if result.success and expected_substring in result.plsql_code:
                print(f"✓ {name:20s} - PASSED")
                passed += 1
            else:
                print(f"✗ {name:20s} - FAILED")
                print(f"  Expected substring: {expected_substring}")
                print(f"  Generated: {result.plsql_code[:100]}...")
                failed += 1
        except Exception as e:
            print(f"✗ {name:20s} - ERROR: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 60)

    # Show some example translations
    print("\nExample translations:")
    print("-" * 60)

    examples = [
        ("Chr(65)", DataType.STRING),
        ("DatePart('yyyy', {OrderDate})", DataType.NUMBER),
        ("IIF({Amount} > 1000, 'High', IIF({Amount} > 100, 'Medium', 'Low'))", DataType.STRING),
    ]

    for expr, ret_type in examples:
        formula = Formula(
            name="Example",
            expression=expr,
            return_type=ret_type,
            syntax=FormulaSyntax.CRYSTAL,
        )
        result = translator.translate(formula)
        print(f"\nCrystal: {expr}")
        print(f"Oracle: {result.plsql_code}")
        if result.warnings:
            print(f"Warnings: {', '.join(result.warnings)}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_new_functions()
    sys.exit(0 if failed == 0 else 1)
