#!/bin/bash
#
# RPT-to-RDF Converter - Shell Wrapper
# Converts Crystal Reports 14 (.rpt) to Oracle Reports 12c (.rdf)
#
# Usage:
#   ./rpt-to-rdf.sh convert <input> <output> [options]
#   ./rpt-to-rdf.sh analyze <input> [options]
#   ./rpt-to-rdf.sh check-config
#   ./rpt-to-rdf.sh --help
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python not found. Please install Python 3.9+"
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

# Check if virtual environment exists and activate it
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Run the converter
exec $PYTHON -m src.main "$@"
