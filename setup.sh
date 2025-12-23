#!/bin/bash
#
# RPT-to-RDF Converter - Setup Script
# Creates virtual environment and installs dependencies
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "  RPT-to-RDF Setup"
echo "================================"
echo

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
echo "[+] Found Python: $PYTHON_VERSION"

# Create virtual environment
if [ -d "venv" ]; then
    echo "[*] Virtual environment already exists"
else
    echo "[*] Creating virtual environment..."
    $PYTHON -m venv venv
    echo "[+] Virtual environment created"
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[*] Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "[*] Installing dependencies..."
pip install -r requirements.txt -q

echo "[+] Dependencies installed"

# Create directories if they don't exist
echo "[*] Creating directories..."
mkdir -p input output logs temp
touch input/.gitkeep output/.gitkeep logs/.gitkeep temp/.gitkeep

# Build Java RptToXml if Java is available
if command -v java &> /dev/null; then
    echo "[*] Java found, checking RptToXml Java build..."
    if [ -d "tools/RptToXmlJava" ]; then
        if [ ! -f "tools/RptToXmlJava/target/RptToXml.jar" ]; then
            echo "[*] Building RptToXml Java..."
            cd tools/RptToXmlJava
            if [ -f "build.sh" ]; then
                chmod +x build.sh
                ./build.sh
            fi
            cd "$SCRIPT_DIR"
        else
            echo "[+] RptToXml Java already built"
        fi
    fi
else
    echo "[!] Java not found - RptToXml Java edition will not be available"
fi

echo
echo "================================"
echo "  Setup Complete!"
echo "================================"
echo
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo
echo "To run the converter:"
echo "  ./rpt-to-rdf.sh --help"
echo "  ./rpt-to-rdf.sh check-config"
echo "  ./rpt-to-rdf.sh convert ./input ./output --mock"
echo
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo
