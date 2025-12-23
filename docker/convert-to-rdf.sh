#!/bin/bash
#
# Convert Oracle Reports XML to RDF using Docker or remote Oracle server
#
# Usage:
#   ./convert-to-rdf.sh <input.xml> <output.rdf>
#   ./convert-to-rdf.sh --batch <input_dir> <output_dir>
#
# Environment variables:
#   ORACLE_CONTAINER  - Docker container name (default: oracle-reports)
#   ORACLE_HOST       - Remote Oracle host (if not using Docker)
#   ORACLE_USER       - Database user (default: system)
#   ORACLE_PWD        - Database password
#   ORACLE_SERVICE    - Database service (default: XE)
#

set -e

# Configuration
CONTAINER_NAME="${ORACLE_CONTAINER:-oracle-reports}"
ORACLE_USER="${ORACLE_USER:-system}"
ORACLE_SERVICE="${ORACLE_SERVICE:-XE}"
ORACLE_HOME="${ORACLE_HOME:-/u01/oracle/product/12c}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <input.xml> <output.rdf>"
    echo "       $0 --batch <input_dir> <output_dir>"
    echo ""
    echo "Environment variables:"
    echo "  ORACLE_CONTAINER  Docker container name (default: oracle-reports)"
    echo "  ORACLE_PWD        Database password (required)"
    echo "  ORACLE_USER       Database user (default: system)"
    echo "  ORACLE_SERVICE    Database service (default: XE)"
    exit 1
}

check_docker() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}Error: Docker container '${CONTAINER_NAME}' is not running${NC}"
        echo "Start it with: docker-compose up -d"
        exit 1
    fi
}

convert_single() {
    local input_xml="$1"
    local output_rdf="$2"

    if [ ! -f "$input_xml" ]; then
        echo -e "${RED}Error: Input file not found: $input_xml${NC}"
        return 1
    fi

    local basename=$(basename "$input_xml")
    local rdf_basename=$(basename "$output_rdf")

    echo -e "${YELLOW}Converting: $basename -> $rdf_basename${NC}"

    # Copy XML to container
    docker cp "$input_xml" "${CONTAINER_NAME}:/tmp/${basename}"

    # Build connection string
    local conn="${ORACLE_USER}/${ORACLE_PWD}@oracle-db:1521/${ORACLE_SERVICE}"

    # Run rwconverter
    docker exec "${CONTAINER_NAME}" /bin/bash -c "
        export ORACLE_HOME=${ORACLE_HOME}
        export PATH=\$ORACLE_HOME/bin:\$PATH
        cd ${ORACLE_HOME}/bin
        ./rwconverter \
            userid=${conn} \
            stype=xmlfile \
            source=/tmp/${basename} \
            dtype=rdffile \
            dest=/tmp/${rdf_basename} \
            batch=yes \
            overwrite=yes
    "

    # Copy RDF back
    docker cp "${CONTAINER_NAME}:/tmp/${rdf_basename}" "$output_rdf"

    # Cleanup temp files in container
    docker exec "${CONTAINER_NAME}" rm -f "/tmp/${basename}" "/tmp/${rdf_basename}"

    echo -e "${GREEN}Created: $output_rdf${NC}"
}

convert_batch() {
    local input_dir="$1"
    local output_dir="$2"

    if [ ! -d "$input_dir" ]; then
        echo -e "${RED}Error: Input directory not found: $input_dir${NC}"
        exit 1
    fi

    mkdir -p "$output_dir"

    local count=0
    local success=0
    local failed=0

    for xml_file in "$input_dir"/*.xml; do
        [ -e "$xml_file" ] || continue

        local basename=$(basename "$xml_file" .xml)
        local rdf_file="${output_dir}/${basename}.rdf"

        count=$((count + 1))

        if convert_single "$xml_file" "$rdf_file"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
    done

    echo ""
    echo -e "${GREEN}Batch conversion complete${NC}"
    echo "  Total: $count"
    echo "  Success: $success"
    echo "  Failed: $failed"
}

# Main
if [ $# -lt 2 ]; then
    usage
fi

# Check for required password
if [ -z "$ORACLE_PWD" ]; then
    echo -e "${RED}Error: ORACLE_PWD environment variable is required${NC}"
    echo "Set it with: export ORACLE_PWD=your_password"
    exit 1
fi

check_docker

if [ "$1" = "--batch" ]; then
    if [ $# -lt 3 ]; then
        usage
    fi
    convert_batch "$2" "$3"
else
    convert_single "$1" "$2"
fi
