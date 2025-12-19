#!/bin/bash
#
# RptToXml Setup Script (macOS/Linux Preparation)
#
# This script prepares the RptToXml source code for building on Windows.
# Since RptToXml requires Crystal Reports .NET assemblies, it can only be
# built and run on Windows. This script helps with preparation steps that
# can be done on macOS/Linux.
#
# Usage:
#   ./setup_rpttoxml.sh [--clone-only] [--output-dir <dir>]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/RptToXml"

# Parse arguments
CLONE_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --clone-only)
            CLONE_ONLY=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--clone-only] [--output-dir <dir>]"
            echo ""
            echo "Options:"
            echo "  --clone-only    Only clone the repository, don't attempt to build"
            echo "  --output-dir    Directory to clone/install to (default: ./RptToXml)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${BLUE}========================================"
echo -e "  RptToXml Setup Script (macOS/Linux)"
echo -e "========================================${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     MACHINE="Linux";;
    Darwin*)    MACHINE="macOS";;
    CYGWIN*)    MACHINE="Cygwin";;
    MINGW*)     MACHINE="MinGW";;
    MSYS*)      MACHINE="MSYS";;
    *)          MACHINE="UNKNOWN:$OS"
esac

echo -e "${CYAN}[*] Detected OS: $MACHINE${NC}"

# Warning for non-Windows systems
if [[ "$MACHINE" != "Cygwin" && "$MACHINE" != "MinGW" && "$MACHINE" != "MSYS" ]]; then
    echo ""
    echo -e "${YELLOW}[!] WARNING: RptToXml can only be built and run on Windows${NC}"
    echo ""
    echo "RptToXml requires:"
    echo "  - Windows 10/11 or Windows Server"
    echo "  - .NET Framework 4.0+"
    echo "  - SAP Crystal Reports Runtime (64-bit)"
    echo ""
    echo "This script will clone the repository so you can:"
    echo "  1. Transfer it to a Windows machine for building"
    echo "  2. Use it in a Windows VM or container"
    echo "  3. Build it via CI/CD on a Windows agent"
    echo ""
fi

# Check for Git
echo -e "${CYAN}[*] Checking for Git...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}[-] Git is not installed${NC}"
    echo "Please install Git:"
    if [[ "$MACHINE" == "macOS" ]]; then
        echo "  brew install git"
    else
        echo "  sudo apt-get install git  # Debian/Ubuntu"
        echo "  sudo yum install git      # CentOS/RHEL"
    fi
    exit 1
fi
echo -e "${GREEN}[+] Git found: $(which git)${NC}"

# Check if already cloned
if [[ -d "$OUTPUT_DIR" && -d "$OUTPUT_DIR/.git" ]]; then
    echo -e "${CYAN}[*] RptToXml repository already exists at: $OUTPUT_DIR${NC}"
    echo -e "${CYAN}[*] Pulling latest changes...${NC}"
    cd "$OUTPUT_DIR"
    git pull origin master || git pull origin main || echo "Could not pull, using existing version"
    cd "$SCRIPT_DIR"
else
    # Clone the repository
    echo -e "${CYAN}[*] Cloning RptToXml repository...${NC}"
    git clone https://github.com/ajryan/RptToXml.git "$OUTPUT_DIR"
    echo -e "${GREEN}[+] Repository cloned to: $OUTPUT_DIR${NC}"
fi

# Display repository info
echo ""
echo -e "${CYAN}[*] Repository contents:${NC}"
ls -la "$OUTPUT_DIR"

# Check for solution file
if [[ -f "$OUTPUT_DIR/RptToXml.sln" ]]; then
    echo -e "${GREEN}[+] Found solution file: RptToXml.sln${NC}"
else
    SLN_FILE=$(find "$OUTPUT_DIR" -name "*.sln" -type f | head -1)
    if [[ -n "$SLN_FILE" ]]; then
        echo -e "${GREEN}[+] Found solution file: $SLN_FILE${NC}"
    else
        echo -e "${YELLOW}[!] No .sln file found - repository structure may have changed${NC}"
    fi
fi

if [[ "$CLONE_ONLY" == true ]]; then
    echo ""
    echo -e "${GREEN}[+] Clone complete. Use the PowerShell script on Windows to build.${NC}"
    exit 0
fi

# Try to build with Mono (if available) - usually won't work due to Crystal Reports dependencies
echo ""
echo -e "${CYAN}[*] Checking for Mono (optional)...${NC}"

if command -v msbuild &> /dev/null || command -v xbuild &> /dev/null; then
    echo -e "${YELLOW}[!] Mono build tools detected, but RptToXml requires Windows-specific Crystal Reports DLLs${NC}"
    echo "Building with Mono will likely fail due to missing dependencies."
    echo ""

    read -p "Attempt Mono build anyway? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}[*] Attempting build with Mono...${NC}"
        cd "$OUTPUT_DIR"

        # Try xbuild (older Mono) or msbuild
        if command -v msbuild &> /dev/null; then
            msbuild RptToXml.sln /p:Configuration=Release || {
                echo -e "${RED}[-] Build failed (expected - Crystal Reports not available)${NC}"
            }
        elif command -v xbuild &> /dev/null; then
            xbuild RptToXml.sln /p:Configuration=Release || {
                echo -e "${RED}[-] Build failed (expected - Crystal Reports not available)${NC}"
            }
        fi

        cd "$SCRIPT_DIR"
    fi
else
    echo -e "${CYAN}[*] Mono not installed (not required for Windows build)${NC}"
fi

# Create a helper script for Windows
echo ""
echo -e "${CYAN}[*] Creating Windows build helper script...${NC}"

cat > "$OUTPUT_DIR/build_windows.bat" << 'EOFBAT'
@echo off
REM Windows Build Script for RptToXml
REM Run this on a Windows machine with Visual Studio installed

echo Building RptToXml...

REM Try to find MSBuild
set MSBUILD=
for %%i in (
    "%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles%\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles%\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles%\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    "%ProgramFiles(x86)%\MSBuild\14.0\Bin\MSBuild.exe"
) do (
    if exist %%i (
        set MSBUILD=%%i
        goto :found
    )
)

echo ERROR: MSBuild not found. Please install Visual Studio.
exit /b 1

:found
echo Using MSBuild: %MSBUILD%

REM Build
"%MSBUILD%" RptToXml.sln /p:Configuration=Release /verbosity:minimal

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build successful!
echo Executable location: bin\Release\RptToXml.exe
dir /b bin\Release\*.exe 2>nul

pause
EOFBAT

echo -e "${GREEN}[+] Created: $OUTPUT_DIR/build_windows.bat${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================"
echo -e "  Setup Complete!"
echo -e "========================================${NC}"
echo ""
echo "Repository cloned to: $OUTPUT_DIR"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo "Option 1: Build on Windows directly"
echo "  1. Copy the $OUTPUT_DIR folder to a Windows machine"
echo "  2. Install Visual Studio 2019+ with '.NET desktop development'"
echo "  3. Install SAP Crystal Reports for Visual Studio (SP28+)"
echo "  4. Run: build_windows.bat"
echo "  5. Copy bin/Release/RptToXml.exe back to this machine"
echo ""
echo "Option 2: Use the PowerShell script on Windows"
echo "  1. Copy tools/setup_rpttoxml.ps1 to Windows"
echo "  2. Run: powershell -ExecutionPolicy Bypass -File setup_rpttoxml.ps1"
echo ""
echo "Option 3: Use a Windows VM or Docker container"
echo "  - Use a Windows container with Visual Studio Build Tools"
echo "  - Mount this directory and run the build"
echo ""
echo -e "${YELLOW}Note: The built RptToXml.exe must also be run on Windows${NC}"
echo "because it requires Crystal Reports runtime DLLs."
echo ""

# Create .gitignore for the cloned repo (to avoid committing build artifacts)
if [[ ! -f "$OUTPUT_DIR/.gitignore" ]]; then
    cat > "$OUTPUT_DIR/.gitignore" << 'EOFGIT'
bin/
obj/
*.exe
*.dll
*.pdb
*.user
*.suo
.vs/
packages/
EOFGIT
    echo -e "${CYAN}[*] Created .gitignore in RptToXml directory${NC}"
fi
