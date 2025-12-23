#!/bin/bash
#
# Build the RptToXml Docker image
#
# Prerequisites:
#   - RptToXml Java project must be built first (../tools/RptToXmlJava/build.sh)
#   - Crystal Reports SDK JARs must be in ../tools/RptToXmlJava/lib/
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RPTTOXML_DIR="$PROJECT_ROOT/tools/RptToXmlJava"

echo "================================"
echo "  Building RptToXml Docker Image"
echo "================================"
echo

# Check if RptToXml JAR exists
if [ ! -f "$RPTTOXML_DIR/target/RptToXml.jar" ]; then
    echo "[!] RptToXml.jar not found. Building..."
    cd "$RPTTOXML_DIR"
    ./build.sh
    cd "$SCRIPT_DIR"
fi

# Copy files to docker context
echo "[*] Copying files to Docker context..."
mkdir -p "$SCRIPT_DIR/target"
mkdir -p "$SCRIPT_DIR/lib"

cp "$RPTTOXML_DIR/target/RptToXml.jar" "$SCRIPT_DIR/target/"
cp "$RPTTOXML_DIR/lib/"*.jar "$SCRIPT_DIR/lib/"
cp "$RPTTOXML_DIR/CRConfig.xml" "$SCRIPT_DIR/" 2>/dev/null || echo '<?xml version="1.0" encoding="utf-8"?>
<CrystalReportEngine-configuration>
    <timeout>0</timeout>
</CrystalReportEngine-configuration>' > "$SCRIPT_DIR/CRConfig.xml"

# Build Docker image
echo "[*] Building Docker image..."
docker build -t rpttoxml:latest "$SCRIPT_DIR"

# Cleanup
echo "[*] Cleaning up..."
rm -rf "$SCRIPT_DIR/target" "$SCRIPT_DIR/lib" "$SCRIPT_DIR/CRConfig.xml"

echo
echo "================================"
echo "  Build Complete!"
echo "================================"
echo
echo "Usage:"
echo "  docker run -v \$(pwd)/input:/reports/input -v \$(pwd)/output:/reports/output \\"
echo "    rpttoxml:latest /reports/input/report.rpt /reports/output/report.xml"
echo
echo "Or use the wrapper script:"
echo "  ./extract-rpt.sh input/report.rpt output/report.xml"
echo
