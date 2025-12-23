#!/bin/bash
#
# RptToXml wrapper script - Cross-platform Crystal Reports to XML extractor
#
# This script automatically handles the Crystal Reports SDK path resolution issue
# on all platforms (Windows, Linux, macOS) by creating the proper WEB-INF structure.
#
# Usage:
#   ./rpttoxml.sh <input.rpt> [output.xml]
#   ./rpttoxml.sh -r <directory>
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_PATH="$SCRIPT_DIR/target/RptToXml.jar"
LIB_PATH="$SCRIPT_DIR/lib"

# Check if JAR exists
if [ ! -f "$JAR_PATH" ]; then
    echo "Error: RptToXml.jar not found. Please run ./build.sh first."
    exit 1
fi

# Show help
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "RptToXml - Crystal Reports to XML Extractor"
    echo ""
    echo "Usage:"
    echo "  $0 <input.rpt> [output.xml]"
    echo "  $0 -r <directory>          Process all .rpt files recursively"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -r             Recursive directory processing"
    echo ""
    echo "Examples:"
    echo "  $0 report.rpt"
    echo "  $0 report.rpt output.xml"
    echo "  $0 -r ./reports/"
    exit 0
fi

# Handle recursive directory mode
if [ "$1" = "-r" ] || [ "$1" = "--recursive" ]; then
    if [ -z "$2" ]; then
        echo "Error: Directory path required for recursive mode"
        exit 1
    fi

    DIR_PATH="$2"
    if [ ! -d "$DIR_PATH" ]; then
        echo "Error: Not a directory: $DIR_PATH"
        exit 1
    fi

    # Find all .rpt files and process them
    SUCCESS=0
    FAILED=0

    while IFS= read -r -d '' rpt_file; do
        # Remove .rpt extension (case insensitive) and add .xml
        output_file=$(echo "$rpt_file" | sed 's/\.[rR][pP][tT]$/.xml/')

        if "$0" "$rpt_file" "$output_file"; then
            ((SUCCESS++)) || true
        else
            ((FAILED++)) || true
        fi
    done < <(find "$DIR_PATH" -type f \( -name "*.rpt" -o -name "*.RPT" \) -print0)

    echo ""
    echo "Completed: $SUCCESS successful, $FAILED failed"
    exit 0
fi

# Single file mode
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.rpt> [output.xml]"
    echo "       $0 -r <directory>"
    exit 1
fi

INPUT_FILE="$1"
INPUT_NAME=$(basename "$INPUT_FILE")

# Get absolute path of input
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Determine output path
if [ -n "$2" ]; then
    OUTPUT_FILE="$2"
    # Make output path absolute if not already
    if [[ "$OUTPUT_FILE" != /* ]]; then
        OUTPUT_FILE="$(pwd)/$OUTPUT_FILE"
    fi
else
    # Remove .rpt extension (case insensitive) and add .xml
    OUTPUT_FILE=$(echo "$INPUT_FILE" | sed 's/\.[rR][pP][tT]$/.xml/')
fi

# Create temp directory with WEB-INF structure
# This is required because the Crystal Reports SDK resolves paths relative to the JAR location
# and expects JARs to be in WEB-INF/lib/ with config in WEB-INF/classes/
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create WEB-INF structure
mkdir -p "$TEMP_DIR/WEB-INF/lib"
mkdir -p "$TEMP_DIR/WEB-INF/classes"

# Copy JARs to WEB-INF/lib
cp "$JAR_PATH" "$TEMP_DIR/WEB-INF/lib/"
cp "$LIB_PATH"/*.jar "$TEMP_DIR/WEB-INF/lib/"

# Create CRConfig.xml in WEB-INF/classes
cat > "$TEMP_DIR/WEB-INF/classes/CRConfig.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<CrystalReportEngine-configuration>
    <timeout>0</timeout>
</CrystalReportEngine-configuration>
EOF

# Copy the report file to the same directory as JARs (critical for path resolution!)
cp "$INPUT_FILE" "$TEMP_DIR/$INPUT_NAME"

echo "Processing: $INPUT_FILE"

# Build classpath pointing to WEB-INF/lib
CLASSPATH="$TEMP_DIR/WEB-INF/lib/RptToXml.jar"
for jar in "$TEMP_DIR/WEB-INF/lib"/*.jar; do
    CLASSPATH="$CLASSPATH:$jar"
done
CLASSPATH="$CLASSPATH:$TEMP_DIR/WEB-INF/classes"

# Save current directory
ORIG_DIR="$(pwd)"

# Run from the temp directory (so relative paths work)
cd "$TEMP_DIR"

# Run the extractor with just the filename (SDK resolves relative to JAR)
# Suppress the native access warnings from newer Java versions
java -cp "$CLASSPATH" \
    --enable-native-access=ALL-UNNAMED 2>/dev/null \
    com.rpttoxml.RptToXml "$INPUT_NAME" "$OUTPUT_FILE" || \
java -cp "$CLASSPATH" \
    com.rpttoxml.RptToXml "$INPUT_NAME" "$OUTPUT_FILE"

# Return to original directory
cd "$ORIG_DIR"

echo "Output: $OUTPUT_FILE"
