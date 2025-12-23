#!/bin/bash
# Test runner script for RPT-to-RDF converter

# Activate virtual environment
source venv/bin/activate

echo "Running unit tests for RPT-to-RDF Converter..."
echo "================================================"

# Run all tests with verbose output
echo -e "\n--- Running Formula Translator Tests ---"
python -m pytest tests/test_formula_translator.py -v

echo -e "\n--- Running Type Mapper Tests ---"
python -m pytest tests/test_type_mapper.py -v

echo -e "\n--- Running Layout Mapper Tests ---"
python -m pytest tests/test_layout_mapper.py -v

echo -e "\n--- Running Integration Tests ---"
python -m pytest tests/test_integration.py -v

echo -e "\n--- Running All Tests with Coverage ---"
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo -e "\n================================================"
echo "Test run complete!"
