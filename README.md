# RPT to RDF Converter

A Python-based batch conversion tool for converting Crystal Reports 14 (.rpt) files to Oracle Reports 12c (.rdf) files, with integrated data migration utilities for Microsoft Access databases.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Docker-Based Extraction](#docker-based-extraction)
- [Data Migration (MDB to Oracle)](#data-migration-mdb-to-oracle)
- [Schema Extraction](#schema-extraction)
- [Configuration](#configuration)
- [Formula Translation](#formula-translation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)

## Features

### Report Conversion
- **Batch Processing**: Convert 200+ reports without manual intervention
- **Formula Translation**: Automatic conversion of Crystal formulas to PL/SQL
- **Layout Mapping**: Crystal sections mapped to Oracle frames
- **Parameter Conversion**: Full parameter support with type mapping
- **Error Handling**: Partial conversion with detailed logging
- **Progress Tracking**: Rich console output with progress bars
- **Reporting**: HTML, CSV, and JSON conversion reports

### Data Migration
- **MDB Extraction**: Extract data from Microsoft Access databases
- **Oracle DDL Generation**: Generate CREATE TABLE statements
- **Data Export**: CSV, INSERT statements, and SQL*Loader files
- **Schema Analysis**: Analyze Crystal Reports to determine required database schema

## Architecture

The converter uses a 5-stage pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONVERSION PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [RPT Files]                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────┐                                                       │
│  │ 1. EXTRACTION    │  RptToXml (Docker/Java) → XML extraction              │
│  │    MODULE        │  Output: Intermediate XML per report                  │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 2. PARSING       │  Parse Crystal XML → Internal Report Model            │
│  │    MODULE        │  Extract: queries, fields, formulas, params, layout   │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 3. TRANSFORMATION│  Map Crystal elements → Oracle Reports elements       │
│  │    ENGINE        │  Convert: formulas, types, sections, connections      │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 4. GENERATION    │  Generate Oracle Reports XML format                   │
│  │    MODULE        │  Output: Oracle-compatible XML files                  │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │ 5. CONVERSION    │  rwconverter XML → RDF (binary)                       │
│  │    MODULE        │  Output: Final .rdf files                             │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  [RDF Files]                                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Platform Requirements

| Stage | Component | Windows | Linux | macOS |
|-------|-----------|---------|-------|-------|
| **1. Extraction** | RptToXml (Docker) | ✅ | ✅ | ✅ |
| **1. Extraction** | RptToXml (Java native) | ✅ | ✅ | ❌ Use Docker |
| **2-4. Transform** | Python pipeline | ✅ | ✅ | ✅ |
| **5. RDF Generation** | Oracle rwconverter | ✅ | ✅ | ⚠️ Docker required |

> **Note for macOS users**: The Crystal Reports Java SDK has path resolution issues on macOS.
> Use the provided Docker container (`docker/rpttoxml/`) for the extraction step.

## Installation

### Prerequisites

- **Python 3.9+** - For the main conversion pipeline
- **Docker** - Recommended for RPT extraction (required on macOS)
- **Java 11+** - Only if running Java extractor natively (Windows/Linux)
- **Oracle Reports 12c** - For final RDF generation (optional, can use `--skip-rdf`)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd RPT-to-RDF

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate.bat   # Windows

pip install -r requirements.txt

# Build Docker image for RPT extraction (recommended)
cd docker/rpttoxml
docker build -t rpttoxml:latest .
cd ../..
```

### Crystal Reports SDK Setup (for Docker)

The Docker image requires the Crystal Reports Java SDK libraries:

1. Download **Crystal Reports for Eclipse** from [SAP Software Downloads](https://support.sap.com/en/my-support/software-downloads.html)
   - Search for "Crystal Reports, developer version for Microsoft Visual Studio"
   - Download the Java/Eclipse runtime (CR4ERL*.zip)

2. Extract and copy JARs to the Docker build context:
```bash
# Extract the SDK
unzip CR4ERL31_0-80004572.zip -d /tmp/crystal-sdk

# Copy required JARs
cp /tmp/crystal-sdk/lib/*.jar docker/rpttoxml/lib/
```

3. Build the Docker image:
```bash
cd docker/rpttoxml
docker build -t rpttoxml:latest .
```

### Verify Installation

```bash
# Check CLI is working
source venv/bin/activate
python -m src.main --help

# Check Docker image
docker run --rm rpttoxml:latest --help

# Check configuration
python -m src.main check-config
```

## Quick Start

### 1. Extract RPT Files to XML (using Docker)

```bash
# Single file
./docker/rpttoxml/extract-rpt.sh input/report.rpt output/

# All files in directory
./docker/rpttoxml/extract-rpt.sh input/ output/
```

### 2. Run Full Conversion Pipeline

```bash
source venv/bin/activate

# With mock mode (no Oracle required) - good for testing
python -m src.main convert ./input/ ./output/ --mock

# With Docker extraction, skip RDF generation
python -m src.main convert ./input/ ./output/ --skip-rdf

# Full pipeline (requires Oracle Reports)
python -m src.main convert ./input/ ./output/
```

### 3. Review Results

After conversion, check the generated reports in the logs directory:
- `conversion_report_*.html` - Detailed HTML report
- `conversion_summary_*.csv` - CSV summary for tracking
- `conversion_details_*.json` - Full JSON details

## CLI Commands

### Main Commands

```bash
# Convert RPT to RDF
python -m src.main convert <input> <output> [options]

# Analyze reports without converting
python -m src.main analyze <input>

# Validate a converted RDF file
python -m src.main validate <rdf_file>

# Check configuration
python -m src.main check-config

# Extract schema requirements from Crystal Reports XML
python -m src.main extract-schema <xml_path> [options]

# Extract data from Microsoft Access MDB files
python -m src.main extract-mdb <mdb_path> [options]
```

### Convert Options

| Option | Description |
|--------|-------------|
| `-c, --config` | Path to configuration file |
| `-w, --workers` | Number of parallel workers (default: 4) |
| `-r, --recursive` | Process subdirectories (default: true) |
| `--dry-run` | Analyze without converting |
| `--mock` | Use mock converters for testing |
| `--skip-rdf` | Skip RDF conversion (output Oracle XML only) |
| `-v, --verbose` | Enable verbose output |

### Examples

```bash
# Test mode with mock extractors
python -m src.main convert ./input/ ./output/ --mock

# Docker extraction, generate Oracle XML only (no rwconverter needed)
python -m src.main convert ./input/ ./output/ --skip-rdf

# Dry run to see what would be converted
python -m src.main convert ./input/ ./output/ --dry-run

# Full conversion with 8 parallel workers
python -m src.main convert ./input/ ./output/ --workers 8
```

## Docker-Based Extraction

The Docker container provides a cross-platform solution for extracting Crystal Reports to XML.

### Why Docker?

The Crystal Reports Java SDK has specific requirements:
- JARs must be in a `WEB-INF/lib/` directory structure
- Report files must be in the same directory as the JARs
- Path resolution is relative to JAR location

The Docker container handles all of this automatically.

### Building the Docker Image

```bash
cd docker/rpttoxml

# Copy Crystal Reports SDK JARs to lib/ directory first
# (see Installation section)

docker build -t rpttoxml:latest .
```

### Using the Docker Extractor

```bash
# Using the wrapper script (recommended)
./docker/rpttoxml/extract-rpt.sh input/report.rpt output/

# Direct Docker command
docker run --rm \
  -v "/path/to/report.rpt:/app/report.rpt:ro" \
  -v "/path/to/output:/reports/output" \
  rpttoxml:latest \
  "report.rpt" \
  "/reports/output/report.xml"
```

### Batch Extraction

```bash
# Extract all RPT files in a directory
./docker/rpttoxml/extract-rpt.sh ./input/ ./output/

# This will create XML files for each RPT file:
# input/report1.rpt → output/report1.xml
# input/report2.rpt → output/report2.xml
```

## Data Migration (MDB to Oracle)

If your Crystal Reports use a Microsoft Access database as the data source, you'll need to migrate the data to Oracle. The `extract-mdb` command provides comprehensive data migration tools.

### View Database Summary

```bash
python -m src.main extract-mdb ./input/database.mdb
```

Output:
```
============================================================
MDB DATABASE SUMMARY
============================================================
Source: database.mdb
Total tables: 41
User tables: 40

USER TABLES:
----------------------------------------
  cities: 90 rows, 2 columns
  countries: 249 rows, 6 columns
  sports_teams: 164 rows, 9 columns
  ...

Total rows: 171,370
```

### Generate Oracle DDL

```bash
# Generate CREATE TABLE statements
python -m src.main extract-mdb ./input/database.mdb --mode ddl --schema REPORTS

# Save to file
python -m src.main extract-mdb ./input/database.mdb --mode ddl --schema REPORTS -o schema.sql
```

### Export Data

```bash
# Export single table to CSV
python -m src.main extract-mdb ./input/database.mdb --mode csv -t sports_teams

# Generate INSERT statements
python -m src.main extract-mdb ./input/database.mdb --mode inserts -t sports_teams --schema REPORTS

# Generate SQL*Loader control file
python -m src.main extract-mdb ./input/database.mdb --mode sqlldr -t sports_teams --schema REPORTS
```

### Full Export (Recommended)

Export everything needed for Oracle migration:

```bash
python -m src.main extract-mdb ./input/database.mdb --mode all --schema REPORTS -o ./oracle_export/
```

This creates:
```
oracle_export/
├── schema.sql              # CREATE TABLE statements
├── data/                   # CSV files for each table
│   ├── sports_teams.csv
│   ├── cities.csv
│   └── ...
└── sqlldr/                 # SQL*Loader control files
    ├── sports_teams.ctl
    ├── cities.ctl
    └── ...
```

### Loading Data into Oracle

```bash
# Option 1: Use SQL*Loader (recommended for large datasets)
cd oracle_export/sqlldr
sqlldr userid=user/pass@db control=sports_teams.ctl

# Option 2: Run INSERT statements directly
sqlplus user/pass@db @../inserts/sports_teams.sql
```

## Schema Extraction

Analyze Crystal Reports XML files to determine what database schema is required.

### Extract Schema Requirements

```bash
# View summary of required tables/columns
python -m src.main extract-schema ./output/

# Generate Oracle DDL
python -m src.main extract-schema ./output/ --ddl --schema REPORTS

# Save DDL to file
python -m src.main extract-schema ./output/ --ddl --schema REPORTS -o required_schema.sql
```

### Example Output

```
============================================================
SCHEMA REQUIREMENTS SUMMARY
============================================================
Reports analyzed: 9
Tables/Views required: 7

VIEW: vw_sports_tabler_output
  Columns: 7
    - id: NUMBER
    - team: VARCHAR2(4000)
    - sport: VARCHAR2(4000)
    ...
```

## Configuration

### Main Settings (`config/settings.yaml`)

```yaml
extraction:
  mode: "docker"  # docker, java, or dotnet
  docker:
    image: "rpttoxml:latest"
  rpttoxml_path: "./tools/RptToXmlJava/rpttoxml.sh"  # For native Java mode
  temp_directory: "./temp"
  timeout_seconds: 120
  parallel_workers: 4
  retry_attempts: 2

oracle:
  mode: "docker"  # docker or native
  home: "/path/to/oracle/home"
  connection: "user/password@database"
  docker:
    container: "oracle-reports"
    oracle_home: "/u01/oracle"

paths:
  input_directory: "./input"
  output_directory: "./output"
  log_directory: "./logs"

conversion:
  on_unsupported_formula: "placeholder"  # placeholder, skip, fail
  formula_prefix: "CF_"
  parameter_prefix: "P_"
```

### Type Mappings

Crystal to Oracle type mappings are defined in `config/type_mappings.yaml`:

| Crystal Type | Oracle Type |
|-------------|-------------|
| String | VARCHAR2(4000) |
| Number | NUMBER |
| Currency | NUMBER(15,2) |
| Date | DATE |
| DateTime | TIMESTAMP |
| Boolean | VARCHAR2(1) |
| Memo | CLOB |
| Blob | BLOB |

## Formula Translation

Crystal formulas are automatically translated to PL/SQL:

| Crystal | Oracle |
|---------|--------|
| `{Table.Field}` | `:FIELD_NAME` |
| `@FormulaName` | `CF_FORMULANAME()` |
| `?Parameter` | `:P_PARAMETER` |
| `Left(str, n)` | `SUBSTR(str, 1, n)` |
| `Right(str, n)` | `SUBSTR(str, -n)` |
| `Mid(str, start, len)` | `SUBSTR(str, start, len)` |
| `IIF(cond, t, f)` | `CASE WHEN cond THEN t ELSE f END` |
| `CurrentDate` | `TRUNC(SYSDATE)` |
| `CurrentDateTime` | `SYSTIMESTAMP` |
| `Year(date)` | `EXTRACT(YEAR FROM date)` |
| `ToText(val)` | `TO_CHAR(val)` |
| `ToNumber(str)` | `TO_NUMBER(str)` |

## Project Structure

```
RPT-to-RDF/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── config.py                  # Configuration management
│   ├── pipeline.py                # Pipeline orchestration
│   ├── extraction/
│   │   ├── rpt_extractor.py       # RPT → XML extraction
│   │   └── crystal_sdk.py         # Crystal SDK interface
│   ├── parsing/
│   │   ├── crystal_parser.py      # Parse Crystal XML
│   │   └── report_model.py        # Internal report model
│   ├── transformation/
│   │   ├── transformer.py         # Main transformer
│   │   ├── formula_translator.py  # Crystal → PL/SQL
│   │   ├── type_mapper.py         # Type mappings
│   │   └── layout_mapper.py       # Layout conversion
│   ├── generation/
│   │   ├── oracle_xml_generator.py # Generate Oracle XML
│   │   └── rdf_converter.py       # rwconverter wrapper
│   └── utils/
│       ├── logger.py              # Logging
│       ├── schema_extractor.py    # Schema analysis
│       └── mdb_extractor.py       # MDB data extraction
│
├── config/
│   ├── settings.yaml              # Main configuration
│   ├── type_mappings.yaml         # Type mappings
│   └── formula_mappings.yaml      # Formula mappings
│
├── docker/
│   └── rpttoxml/
│       ├── Dockerfile             # Docker image definition
│       ├── extract-rpt.sh         # Wrapper script
│       ├── lib/                   # Crystal SDK JARs (add manually)
│       └── README.md              # Docker-specific docs
│
├── tools/
│   └── RptToXmlJava/              # Java-based extractor source
│       ├── src/
│       ├── pom.xml
│       └── build.sh
│
├── input/                         # Input RPT files
├── output/                        # Output XML/RDF files
├── logs/                          # Conversion logs
├── temp/                          # Temporary files
│
├── requirements.txt               # Python dependencies
├── setup.sh                       # Setup script
└── README.md                      # This file
```

## Troubleshooting

### "Unexpected error determining relative path" (Crystal SDK)

This error occurs when the Crystal Reports Java SDK can't find the report file relative to the JAR location.

**Solution**: Use the Docker-based extractor which handles path resolution automatically.

```bash
./docker/rpttoxml/extract-rpt.sh input/report.rpt output/
```

### Docker image won't build

Ensure you've copied the Crystal Reports SDK JARs to `docker/rpttoxml/lib/`:

```bash
ls docker/rpttoxml/lib/
# Should show: CrystalReportsRuntime.jar, jrcerom.jar, etc.
```

### "No module named 'access_parser'"

Install the access-parser library:

```bash
pip install access-parser
```

### Oracle rwconverter not found

Either:
1. Install Oracle Reports 12c and set `ORACLE_HOME`
2. Use `--skip-rdf` to output Oracle XML without RDF conversion
3. Use Docker-based Oracle Reports (configure in settings.yaml)

### Empty data section in generated Oracle XML

The data model transformation is still in development. The layout and structure are converted, but queries may need manual adjustment.

## Known Limitations

### Platform Limitations
- **macOS**: Crystal Reports Java SDK does not work natively. Use Docker.
- **Oracle RDF Generation**: Requires Oracle Reports 12c (rwconverter utility)

### Report Limitations
- Subreports with more than 2 levels of nesting may require manual adjustment
- Some advanced Crystal formula functions require manual conversion
- Cross-tab reports need special handling
- Running totals across groups may need refinement
- Charts and graphs are not fully supported

### Data Migration Limitations
- MDB password-protected databases are not supported
- Some complex Access queries/views may not export correctly
- BLOB fields are exported as hex strings

## Dependencies

### Python Packages
- **click**: CLI framework
- **PyYAML**: Configuration parsing
- **lxml**: XML processing
- **rich**: Console output and progress bars
- **access-parser**: Microsoft Access MDB file parsing

### External Tools
- **Docker**: For cross-platform RPT extraction
- **Java 11+**: For native Java extraction (Windows/Linux only)
- **Oracle Reports 12c**: For RDF generation (optional)

## License

MIT License

## Support

For issues and feature requests, please create an issue in the repository.
