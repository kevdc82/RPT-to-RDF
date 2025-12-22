#!/bin/bash
#
# Build script for RptToXml Java Edition
#
# Usage:
#   ./build.sh          - Build the project
#   ./build.sh clean    - Clean and rebuild
#   ./build.sh run      - Build and run with test file
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  RptToXml Java Edition Builder${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check for Java
if ! command -v java &> /dev/null; then
    echo -e "${RED}Error: Java is not installed${NC}"
    echo "Please install Java 11 or higher"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
echo -e "${GREEN}[+] Java version: $(java -version 2>&1 | head -n 1)${NC}"

# Check for Maven
USE_MAVEN=false
if command -v mvn &> /dev/null; then
    USE_MAVEN=true
    echo -e "${GREEN}[+] Maven found: $(mvn -version | head -n 1)${NC}"
else
    echo -e "${YELLOW}[!] Maven not found - using manual javac compilation${NC}"
fi

# Create output directories
mkdir -p target/classes
mkdir -p target/lib

# Handle command
case "$1" in
    clean)
        echo -e "${BLUE}[*] Cleaning...${NC}"
        rm -rf target/
        mkdir -p target/classes
        mkdir -p target/lib
        echo -e "${GREEN}[+] Clean complete${NC}"
        ;;
    run)
        # Build first, then run
        "$0"  # Recursive call to build
        if [ -z "$2" ]; then
            echo -e "${YELLOW}Usage: ./build.sh run <file.rpt>${NC}"
            exit 1
        fi
        echo ""
        echo -e "${BLUE}[*] Running RptToXml...${NC}"
        java -cp "target/RptToXml.jar:lib/*" com.rpttoxml.RptToXml "$2"
        exit 0
        ;;
esac

if [ "$USE_MAVEN" = true ]; then
    # Maven build
    echo -e "${BLUE}[*] Building with Maven...${NC}"
    mvn clean package -DskipTests -q

    if [ -f "target/RptToXml-1.0.0.jar" ]; then
        cp target/RptToXml-1.0.0.jar target/RptToXml.jar
        echo -e "${GREEN}[+] Build successful!${NC}"
        echo -e "${GREEN}[+] JAR: target/RptToXml.jar${NC}"
    fi
else
    # Manual compilation with javac
    echo -e "${BLUE}[*] Compiling with javac...${NC}"

    # Build classpath from lib directory
    CLASSPATH=""
    for jar in lib/*.jar; do
        if [ -n "$CLASSPATH" ]; then
            CLASSPATH="$CLASSPATH:"
        fi
        CLASSPATH="$CLASSPATH$jar"
    done

    # Compile
    javac -d target/classes \
          -cp "$CLASSPATH" \
          -sourcepath src/main/java \
          src/main/java/com/rpttoxml/*.java

    echo -e "${BLUE}[*] Creating JAR...${NC}"

    # Copy resources
    cp -r src/main/resources/* target/classes/ 2>/dev/null || true

    # Create manifest
    cat > target/MANIFEST.MF << EOF
Manifest-Version: 1.0
Main-Class: com.rpttoxml.RptToXml
Class-Path: lib/CrystalReportsRuntime.jar lib/CrystalCommon2.jar lib/JDBInterface.jar lib/DatabaseConnectors.jar lib/QueryBuilder.jar lib/XMLConnector.jar lib/cvom.jar lib/pfjgraphics.jar lib/logging.jar lib/keycodeDecoder.jar lib/jrcerom.jar lib/webreporting.jar lib/icu4j.jar lib/commons-collections-3.2.2.jar lib/commons-configuration-1.2.jar lib/commons-lang-2.1.jar lib/commons-logging.jar lib/log4j-api.jar lib/log4j-core.jar lib/json.jar lib/xpp3.jar lib/jai_imageio.jar
EOF

    # Create JAR
    jar cfm target/RptToXml.jar target/MANIFEST.MF -C target/classes .

    echo -e "${GREEN}[+] Build successful!${NC}"
    echo -e "${GREEN}[+] JAR: target/RptToXml.jar${NC}"
fi

# Copy lib for distribution
echo -e "${BLUE}[*] Copying libraries...${NC}"
cp -r lib/* target/lib/ 2>/dev/null || true

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Usage:"
echo "  java -jar target/RptToXml.jar <input.rpt> [output.xml]"
echo "  java -jar target/RptToXml.jar -r <directory>"
echo ""
echo "Or use the wrapper script:"
echo "  ./rpttoxml.sh <input.rpt> [output.xml]"
echo ""
