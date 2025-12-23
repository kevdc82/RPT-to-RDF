#!/bin/bash
#
# Extract Crystal Reports RPT file to XML using Docker
#
# Usage:
#   ./extract-rpt.sh <input.rpt> [output.xml]
#   ./extract-rpt.sh --batch <input_dir> <output_dir>
#
# Examples:
#   ./extract-rpt.sh report.rpt
#   ./extract-rpt.sh report.rpt output.xml
#   ./extract-rpt.sh --batch ./input ./output
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="rpttoxml:latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <input.rpt> [output.xml]"
    echo "       $0 --batch <input_dir> <output_dir>"
    echo ""
    echo "Examples:"
    echo "  $0 report.rpt                    # Output to report.xml"
    echo "  $0 report.rpt output.xml         # Specify output file"
    echo "  $0 --batch ./input ./output      # Batch convert directory"
    exit 1
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi

    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        echo -e "${YELLOW}Docker image not found. Building...${NC}"
        "$SCRIPT_DIR/build.sh"
    fi
}

extract_single() {
    local input_file="$1"
    local output_file="$2"

    # Get absolute paths
    input_file="$(cd "$(dirname "$input_file")" && pwd)/$(basename "$input_file")"

    if [ -z "$output_file" ]; then
        output_file="${input_file%.rpt}.xml"
    else
        # Make output path absolute if not already
        if [[ "$output_file" != /* ]]; then
            output_file="$(pwd)/$output_file"
        fi
    fi

    local output_dir="$(dirname "$output_file")"
    local input_name="$(basename "$input_file")"
    local output_name="$(basename "$output_file")"

    # Create output directory if needed
    mkdir -p "$output_dir"

    echo -e "${YELLOW}Extracting: $input_name${NC}"

    # Run Docker container
    # IMPORTANT: The Crystal Reports SDK requires the report file to be in the same
    # directory as the JAR files (/app). We mount the single file directly to /app
    # and use just the filename when opening. The output directory is mounted separately.
    docker run --rm \
        -v "$input_file:/app/$input_name:ro" \
        -v "$output_dir:/reports/output" \
        "$IMAGE_NAME" \
        "$input_name" \
        "/reports/output/$output_name"

    if [ -f "$output_file" ]; then
        echo -e "${GREEN}Created: $output_file${NC}"
    else
        echo -e "${RED}Failed to create output file${NC}"
        return 1
    fi
}

extract_batch() {
    local input_dir="$1"
    local output_dir="$2"

    # Get absolute paths
    input_dir="$(cd "$input_dir" && pwd)"
    mkdir -p "$output_dir"
    output_dir="$(cd "$output_dir" && pwd)"

    echo -e "${YELLOW}Batch extracting from: $input_dir${NC}"
    echo -e "${YELLOW}Output to: $output_dir${NC}"
    echo

    local count=0
    local success=0
    local failed=0

    for rpt_file in "$input_dir"/*.rpt; do
        [ -e "$rpt_file" ] || continue

        local basename="$(basename "$rpt_file" .rpt)"
        local xml_file="$output_dir/${basename}.xml"

        count=$((count + 1))

        if extract_single "$rpt_file" "$xml_file"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
    done

    echo
    echo -e "${GREEN}Batch extraction complete${NC}"
    echo "  Total: $count"
    echo "  Success: $success"
    echo "  Failed: $failed"
}

# Main
if [ $# -lt 1 ]; then
    usage
fi

check_docker

if [ "$1" = "--batch" ]; then
    if [ $# -lt 3 ]; then
        usage
    fi
    extract_batch "$2" "$3"
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
else
    extract_single "$1" "$2"
fi
