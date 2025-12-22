#!/bin/bash
#
# RptToXml wrapper script
#
# Usage:
#   ./rpttoxml.sh <input.rpt> [output.xml]
#   ./rpttoxml.sh -r <directory>
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_PATH="$SCRIPT_DIR/target/RptToXml.jar"
LIB_PATH="$SCRIPT_DIR/lib"

# Check if JAR exists
if [ ! -f "$JAR_PATH" ]; then
    echo "Error: RptToXml.jar not found. Please run ./build.sh first."
    exit 1
fi

# Build classpath
CLASSPATH="$JAR_PATH"
for jar in "$LIB_PATH"/*.jar; do
    CLASSPATH="$CLASSPATH:$jar"
done

# Run
java -cp "$CLASSPATH" com.rpttoxml.RptToXml "$@"
