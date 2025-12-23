#!/bin/bash
# Type checking script for RPT-to-RDF converter
# Run this script to verify all type hints are correct

set -e

echo "========================================="
echo "RPT-to-RDF Type Checking Script"
echo "========================================="
echo ""

# Check if mypy is installed
if ! command -v mypy &> /dev/null; then
    echo "mypy not found. Installing..."
    pip install -q mypy
    echo "✓ mypy installed"
fi

echo "Running mypy type checker..."
echo ""

# Run mypy with configuration from mypy.ini
mypy src/ --config-file mypy.ini

echo ""
echo "========================================="
echo "Type checking complete!"
echo "========================================="
echo ""
echo "To generate detailed reports, run:"
echo "  mypy src/ --html-report .mypy_html"
echo "  mypy src/ --txt-report .mypy_txt"
echo ""
