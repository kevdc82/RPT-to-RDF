<#
.SYNOPSIS
    Downloads and builds RptToXml for RPT to RDF Converter.

.DESCRIPTION
    This script clones the RptToXml repository from GitHub, builds it using
    MSBuild, and copies the executable to the tools directory.

.NOTES
    Prerequisites:
    - Windows 10/11 or Windows Server 2016+
    - Visual Studio 2019+ OR MSBuild (via Build Tools for Visual Studio)
    - .NET Framework 4.0+ SDK
    - SAP Crystal Reports for Visual Studio (SP28+) 64-bit runtime

.EXAMPLE
    .\setup_rpttoxml.ps1

.EXAMPLE
    .\setup_rpttoxml.ps1 -SkipCrystalCheck
#>

param(
    [switch]$SkipCrystalCheck,
    [switch]$Force,
    [string]$OutputDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Status { param($Message) Write-Host "[*] $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[+] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[!] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[-] $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "  RptToXml Setup Script" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Check if running on Windows
if ($env:OS -ne "Windows_NT") {
    Write-Error "This script must be run on Windows."
    Write-Host "RptToXml requires Crystal Reports .NET assemblies which are Windows-only."
    exit 1
}

# Check for existing installation
$rptToXmlExe = Join-Path $OutputDir "RptToXml.exe"
if ((Test-Path $rptToXmlExe) -and -not $Force) {
    Write-Success "RptToXml.exe already exists at: $rptToXmlExe"
    Write-Host "Use -Force to rebuild."
    exit 0
}

# Step 1: Check for Crystal Reports Runtime
Write-Status "Checking for Crystal Reports Runtime..."

if (-not $SkipCrystalCheck) {
    $crystalPaths = @(
        "${env:ProgramFiles}\SAP BusinessObjects\Crystal Reports for .NET Framework*",
        "${env:ProgramFiles(x86)}\SAP BusinessObjects\Crystal Reports for .NET Framework*",
        "${env:ProgramFiles}\SAP\Crystal Reports*",
        "${env:ProgramFiles(x86)}\SAP\Crystal Reports*"
    )

    $crystalFound = $false
    foreach ($path in $crystalPaths) {
        $resolved = Resolve-Path $path -ErrorAction SilentlyContinue
        if ($resolved) {
            Write-Success "Found Crystal Reports at: $resolved"
            $crystalFound = $true
            break
        }
    }

    if (-not $crystalFound) {
        Write-Warning "Crystal Reports Runtime not detected!"
        Write-Host ""
        Write-Host "Please install SAP Crystal Reports for Visual Studio (SP28+) 64-bit:"
        Write-Host "  1. Go to: https://www.sap.com/products/technology-platform/crystal-reports.html"
        Write-Host "  2. Download 'SAP Crystal Reports for Visual Studio (SP28)'"
        Write-Host "  3. Run the installer and select 64-bit runtime"
        Write-Host ""
        Write-Host "Alternatively, use -SkipCrystalCheck to continue anyway."

        $response = Read-Host "Continue without Crystal Reports? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            exit 1
        }
    }
}

# Step 2: Check for Git
Write-Status "Checking for Git..."
$gitPath = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitPath) {
    Write-Error "Git is not installed or not in PATH."
    Write-Host "Please install Git from: https://git-scm.com/download/win"
    exit 1
}
Write-Success "Git found: $($gitPath.Source)"

# Step 3: Check for MSBuild
Write-Status "Checking for MSBuild..."

$msbuildPaths = @(
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\*\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2019\*\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\*\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\*\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\MSBuild\14.0\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\MSBuild\12.0\Bin\MSBuild.exe"
)

$msbuildExe = $null
foreach ($path in $msbuildPaths) {
    $resolved = Resolve-Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($resolved) {
        $msbuildExe = $resolved.Path
        break
    }
}

if (-not $msbuildExe) {
    # Try to find via vswhere
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -requires Microsoft.Component.MSBuild -find MSBuild\**\Bin\MSBuild.exe | Select-Object -First 1
        if ($vsPath) {
            $msbuildExe = $vsPath
        }
    }
}

if (-not $msbuildExe) {
    Write-Error "MSBuild not found!"
    Write-Host ""
    Write-Host "Please install one of the following:"
    Write-Host "  1. Visual Studio 2019+ with '.NET desktop development' workload"
    Write-Host "  2. Build Tools for Visual Studio: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022"
    exit 1
}
Write-Success "MSBuild found: $msbuildExe"

# Step 4: Create temp directory and clone repository
$tempDir = Join-Path $env:TEMP "RptToXml_Build_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Status "Creating temp directory: $tempDir"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    # Clone repository
    Write-Status "Cloning RptToXml repository..."
    Push-Location $tempDir

    git clone --depth 1 https://github.com/ajryan/RptToXml.git 2>&1 | ForEach-Object { Write-Host "    $_" }

    if ($LASTEXITCODE -ne 0) {
        throw "Git clone failed with exit code: $LASTEXITCODE"
    }
    Write-Success "Repository cloned successfully"

    # Build the project
    Write-Status "Building RptToXml (Release configuration)..."
    $slnPath = Join-Path $tempDir "RptToXml\RptToXml.sln"

    if (-not (Test-Path $slnPath)) {
        # Try alternate structure
        $slnPath = Get-ChildItem -Path "$tempDir\RptToXml" -Filter "*.sln" -Recurse | Select-Object -First 1
        if (-not $slnPath) {
            throw "Could not find RptToXml.sln"
        }
        $slnPath = $slnPath.FullName
    }

    Write-Host "    Solution: $slnPath"

    # Restore NuGet packages if needed
    $nuget = Get-Command nuget -ErrorAction SilentlyContinue
    if ($nuget) {
        Write-Status "Restoring NuGet packages..."
        & nuget restore $slnPath 2>&1 | ForEach-Object { Write-Host "    $_" }
    }

    # Build
    & $msbuildExe $slnPath /p:Configuration=Release /p:Platform="Any CPU" /verbosity:minimal 2>&1 | ForEach-Object { Write-Host "    $_" }

    if ($LASTEXITCODE -ne 0) {
        throw "MSBuild failed with exit code: $LASTEXITCODE"
    }
    Write-Success "Build completed successfully"

    # Find the built executable
    Write-Status "Locating built executable..."
    $builtExe = Get-ChildItem -Path "$tempDir\RptToXml" -Filter "RptToXml.exe" -Recurse |
                Where-Object { $_.DirectoryName -like "*Release*" -or $_.DirectoryName -like "*bin*" } |
                Select-Object -First 1

    if (-not $builtExe) {
        # Try any RptToXml.exe
        $builtExe = Get-ChildItem -Path "$tempDir\RptToXml" -Filter "RptToXml.exe" -Recurse | Select-Object -First 1
    }

    if (-not $builtExe) {
        throw "Could not find built RptToXml.exe"
    }

    Write-Success "Found: $($builtExe.FullName)"

    # Copy to output directory
    Write-Status "Copying to output directory: $OutputDir"

    # Ensure output directory exists
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    # Copy executable and any dependencies
    $sourceDir = $builtExe.DirectoryName
    $filesToCopy = @("*.exe", "*.dll", "*.config")

    foreach ($pattern in $filesToCopy) {
        $files = Get-ChildItem -Path $sourceDir -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Copy-Item $file.FullName -Destination $OutputDir -Force
            Write-Host "    Copied: $($file.Name)"
        }
    }

    Write-Success "RptToXml installed successfully!"

} catch {
    Write-Error "Setup failed: $_"
    exit 1
} finally {
    Pop-Location

    # Cleanup temp directory
    Write-Status "Cleaning up temp directory..."
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Verify installation
Write-Host ""
Write-Status "Verifying installation..."
$finalExe = Join-Path $OutputDir "RptToXml.exe"

if (Test-Path $finalExe) {
    Write-Success "RptToXml.exe is ready at: $finalExe"
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  RptToXml.exe <input.rpt> [output.xml]"
    Write-Host "  RptToXml.exe -r <directory>  (recursive)"
    Write-Host ""

    # Test execution
    Write-Status "Testing executable..."
    try {
        $testOutput = & $finalExe --help 2>&1
        Write-Success "Executable runs successfully"
    } catch {
        Write-Warning "Could not run executable - Crystal Reports runtime may be missing"
    }
} else {
    Write-Error "Installation verification failed - RptToXml.exe not found"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
