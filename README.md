# RPT to RDF Converter

A Python-based batch conversion tool for converting Crystal Reports 14 (.rpt) files to Oracle Reports 12c (.rdf) files.

## Features

- **Batch Processing**: Convert 200+ reports without manual intervention
- **Formula Translation**: Automatic conversion of Crystal formulas to PL/SQL
- **Layout Mapping**: Crystal sections mapped to Oracle frames
- **Parameter Conversion**: Full parameter support with type mapping
- **Error Handling**: Partial conversion with detailed logging
- **Progress Tracking**: Rich console output with progress bars
- **Reporting**: HTML, CSV, and JSON conversion reports

## Installation

### Prerequisites

- Python 3.9 or higher
- Crystal Reports Runtime (SAP Crystal Reports for Visual Studio SP28+)
- Oracle Reports 12c with rwconverter utility
- Windows Server (required for Crystal SDK)

### Install from Source

```bash
git clone <repository-url>
cd RPT-to-RDF
pip install -e .
```

### Install Dependencies Only

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Configure the Tool

Edit `config/settings.yaml` with your environment settings:

```yaml
oracle:
  home: "C:\\Oracle\\Middleware\\Oracle_Home"
  connection: "user/password@database"

extraction:
  rpttoxml_path: "./tools/RptToXml/RptToXml.exe"
```

### 2. Run Conversion

```bash
# Convert a single file
python -m src.main convert report.rpt output/report.rdf

# Convert a directory
python -m src.main convert ./input/ ./output/ --workers 8

# Analyze before converting (dry run)
python -m src.main convert ./input/ ./output/ --dry-run

# Use mock mode for testing (no Crystal/Oracle required)
python -m src.main convert ./input/ ./output/ --mock
```

### 3. Review Results

After conversion, check the generated reports in the logs directory:
- `conversion_report_*.html` - Detailed HTML report
- `conversion_summary_*.csv` - CSV summary for tracking
- `conversion_details_*.json` - Full JSON details

## CLI Commands

```bash
# Convert RPT to RDF
rpt-to-rdf convert <input> <output> [options]

# Analyze reports without converting
rpt-to-rdf analyze <input>

# Validate a converted RDF file
rpt-to-rdf validate <rdf_file>

# Check configuration
rpt-to-rdf check-config
```

### Options

| Option | Description |
|--------|-------------|
| `-c, --config` | Path to configuration file |
| `-w, --workers` | Number of parallel workers (default: 4) |
| `-r, --recursive` | Process subdirectories (default: true) |
| `--dry-run` | Analyze without converting |
| `--mock` | Use mock converters for testing |
| `-v, --verbose` | Enable verbose output |

## Architecture

The converter uses a 5-stage pipeline:

```
[RPT Files] → Extraction → Parsing → Transformation → Generation → [RDF Files]
```

1. **Extraction**: RPT → XML using RptToXml
2. **Parsing**: XML → Internal Report Model
3. **Transformation**: Crystal elements → Oracle elements
4. **Generation**: Internal Model → Oracle Reports XML
5. **Conversion**: XML → RDF using rwconverter

## Configuration

### Main Settings (`config/settings.yaml`)

```yaml
extraction:
  rpttoxml_path: "./tools/RptToXml/RptToXml.exe"
  timeout_seconds: 60
  parallel_workers: 4

oracle:
  home: "/path/to/oracle/home"
  connection: "user/password@database"

conversion:
  on_unsupported_formula: "placeholder"  # placeholder, skip, fail
  formula_prefix: "CF_"
  parameter_prefix: "P_"
```

### Type Mappings (`config/type_mappings.yaml`)

Defines Crystal to Oracle type conversions.

### Formula Mappings (`config/formula_mappings.yaml`)

Defines Crystal function to Oracle PL/SQL mappings.

## Formula Translation

Crystal formulas are automatically translated to PL/SQL:

| Crystal | Oracle |
|---------|--------|
| `{Table.Field}` | `:FIELD_NAME` |
| `@FormulaName` | `CF_FORMULANAME()` |
| `?Parameter` | `:P_PARAMETER` |
| `Left(str, n)` | `SUBSTR(str, 1, n)` |
| `IIF(cond, t, f)` | `CASE WHEN cond THEN t ELSE f END` |
| `CurrentDate` | `TRUNC(SYSDATE)` |

## Error Handling

The converter uses a "partial conversion" strategy:

- Converts all possible elements
- Generates placeholders for unsupported features
- Produces detailed logs for manual review
- Creates runnable RDF files (though possibly incomplete)

## Project Structure

```
rpt-to-rdf/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration
│   ├── pipeline.py          # Pipeline orchestration
│   ├── extraction/          # RPT extraction
│   ├── parsing/             # XML parsing
│   ├── transformation/      # Element transformation
│   ├── generation/          # RDF generation
│   └── utils/               # Utilities
├── config/
│   ├── settings.yaml        # Main configuration
│   ├── type_mappings.yaml   # Type mappings
│   └── formula_mappings.yaml # Formula mappings
├── tools/
│   └── RptToXml/            # RptToXml executable
├── tests/                   # Test suite
├── logs/                    # Conversion logs
├── input/                   # Input RPT files
└── output/                  # Output RDF files
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_formula_translator.py
```

## Dependencies

- **click**: CLI framework
- **PyYAML**: Configuration parsing
- **lxml**: XML processing
- **rich**: Console output and progress bars
- **python-dotenv**: Environment variables

## Known Limitations

- Subreports with more than 2 levels of nesting may require manual adjustment
- Some advanced Crystal formula functions require manual conversion
- Cross-tab reports need special handling
- Running totals across groups may need refinement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License

## Support

For issues and feature requests, please create an issue in the repository.
