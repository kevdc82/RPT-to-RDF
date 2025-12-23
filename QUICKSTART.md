# Quick Start Guide

This guide will help you set up and run your first Crystal Reports to Oracle Reports conversion.

## Prerequisites

- Python 3.9 or higher
- Docker (recommended for RPT extraction)
- Git

## Installation

### 1. Clone and Setup

```bash
git clone https://github.com/kevdc82/RPT-to-RDF.git
cd RPT-to-RDF

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -m src.main --help
```

You should see the available commands listed.

## Basic Usage

### Option A: Quick Test (Mock Mode)

Test the pipeline without any external dependencies:

```bash
# Create test directories
mkdir -p input output

# Run with mock mode (simulates extraction and conversion)
python -m src.main convert ./input/ ./output/ --mock
```

### Option B: Convert to Oracle XML (No Oracle Required)

Generate Oracle Reports XML files without needing Oracle Reports installed:

```bash
# Place your .rpt files in ./input/
python -m src.main convert ./input/ ./output/ --skip-rdf
```

This produces Oracle-compatible XML files that can later be converted to RDF using rwconverter.

### Option C: Full Pipeline (Requires Oracle Reports)

```bash
# Configure Oracle home in config/settings.yaml
python -m src.main convert ./input/ ./output/
```

## Docker-Based RPT Extraction

For reliable cross-platform extraction, use the Docker-based extractor.

### 1. Get Crystal Reports SDK

Download the Crystal Reports Java SDK from SAP:
1. Go to [SAP Software Downloads](https://support.sap.com/en/my-support/software-downloads.html)
2. Search for "Crystal Reports, developer version for Microsoft Visual Studio"
3. Download the Java/Eclipse runtime (CR4ERL*.zip)

### 2. Build Docker Image

```bash
# Extract SDK and copy JARs
unzip CR4ERL31_0-80004572.zip -d /tmp/crystal-sdk
cp /tmp/crystal-sdk/lib/*.jar docker/rpttoxml/lib/

# Build image
cd docker/rpttoxml
docker build -t rpttoxml:latest .
cd ../..
```

### 3. Extract RPT Files

```bash
# Single file
./docker/rpttoxml/extract-rpt.sh input/report.rpt output/

# All files in directory
./docker/rpttoxml/extract-rpt.sh input/ output/
```

## Common Workflows

### Analyze Reports Before Converting

```bash
python -m src.main analyze ./input/
```

This shows complexity scores and feature usage without making changes.

### Generate HTML Preview

View a visual representation of converted reports:

```bash
python -m src.main preview ./output/report.xml
# Opens: ./output/report_preview.html
```

### Extract Database Schema

Determine what Oracle tables you need based on report requirements:

```bash
python -m src.main extract-schema ./output/ --ddl --schema REPORTS -o schema.sql
```

### Migrate Access Database

If your reports use an Access (.mdb) database:

```bash
# View database summary
python -m src.main extract-mdb ./data/database.mdb

# Export everything for Oracle
python -m src.main extract-mdb ./data/database.mdb --mode all --schema REPORTS -o ./oracle_export/
```

## Configuration

The main configuration file is `config/settings.yaml`:

```yaml
extraction:
  mode: "docker"  # docker, java, or dotnet
  docker:
    image: "rpttoxml:latest"
  timeout_seconds: 120

oracle:
  home: "/path/to/oracle/home"      # For rwconverter
  connection: "user/password@db"

conversion:
  on_unsupported_formula: "placeholder"  # placeholder, skip, fail
```

## Output Files

After conversion, check the `logs/` directory for:

| File | Description |
|------|-------------|
| `conversion_report_*.html` | Visual report with success/failure details |
| `conversion_summary_*.csv` | Spreadsheet-friendly summary |
| `conversion_details_*.json` | Complete JSON data for automation |

## Troubleshooting

### "Command not found: python"

Use `python3` instead of `python`:
```bash
python3 -m src.main --help
```

### Docker image build fails

Ensure Crystal SDK JARs are in `docker/rpttoxml/lib/`:
```bash
ls docker/rpttoxml/lib/
# Should show: CrystalReportsRuntime.jar, jrcerom.jar, etc.
```

### "No module named 'src'"

Make sure you're in the project root and virtual environment is activated:
```bash
cd RPT-to-RDF
source venv/bin/activate
```

### Conversion produces empty output

Check the logs for error details:
```bash
cat logs/conversion_report_*.html
```

Common issues:
- RPT file is password-protected
- RPT file uses unsupported Crystal version
- Missing database connection for embedded data

## Next Steps

1. **Review converted reports**: Check HTML previews and Oracle XML output
2. **Test in Oracle Reports Builder**: Open XML files to verify structure
3. **Migrate data**: Use extract-mdb to move Access data to Oracle
4. **Generate RDF files**: Run rwconverter on the Oracle XML

## Getting Help

- Check [TODO.md](TODO.md) for known limitations
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
- Review error codes in the output (RPT-XXXX format)
