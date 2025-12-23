# RPT to RDF Converter

A Python-based batch conversion tool for migrating Crystal Reports 14 (.rpt) files to Oracle Reports 12c (.rdf) files.

## Overview

This tool automates the conversion of Crystal Reports to Oracle Reports, handling formula translation, layout mapping, and data migration. It's designed to process 200+ reports with minimal manual intervention.

## Features

| Category | Features |
|----------|----------|
| **Conversion** | Batch processing, parallel execution (configurable workers), partial conversion with detailed logging |
| **Formula Translation** | 50+ Crystal functions → PL/SQL, nested function support, running totals, conditional formatting |
| **Layout** | Sections → frames mapping, coordinate conversion (twips → points), font mapping |
| **Advanced** | Subreports, charts, cross-tab/pivot tables, parameter conversion |
| **Data Migration** | MDB extraction, Oracle DDL generation, CSV/SQL*Loader export |
| **Output** | Oracle XML, RDF (via rwconverter), HTML preview, validation reports |

## Architecture

```
[RPT Files] → Extraction → Parsing → Transformation → Generation → [RDF Files]
                 ↓            ↓            ↓              ↓
              RptToXml    Crystal XML   Oracle Model   Oracle XML/RDF
```

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup and usage instructions.

```bash
# Install
git clone https://github.com/kevdc82/RPT-to-RDF.git
cd RPT-to-RDF
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Convert (XML only, no Oracle required)
python -m src.main convert ./input/ ./output/ --skip-rdf

# Convert with mock mode (testing)
python -m src.main convert ./input/ ./output/ --mock
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `convert <input> <output>` | Convert RPT files to RDF/XML |
| `analyze <input>` | Analyze reports without converting |
| `preview <xml>` | Generate HTML preview |
| `extract-schema <xml>` | Extract database schema requirements |
| `extract-mdb <mdb>` | Extract data from Access database |
| `check-config` | Validate configuration |

### Convert Options

```bash
python -m src.main convert ./input/ ./output/ [OPTIONS]

Options:
  --skip-rdf        Output Oracle XML only (no rwconverter needed)
  --mock            Use mock converters for testing
  --workers N       Parallel workers (default: 4)
  --dry-run         Analyze without converting
  -v, --verbose     Verbose output
```

## Formula Translation

| Crystal | Oracle |
|---------|--------|
| `Left(str, n)` | `SUBSTR(str, 1, n)` |
| `IIF(cond, t, f)` | `CASE WHEN cond THEN t ELSE f END` |
| `CurrentDate` | `TRUNC(SYSDATE)` |
| `{Table.Field}` | `:FIELD_NAME` |
| `@Formula` | `CF_FORMULA()` |

See [src/transformation/formula_translator.py](src/transformation/formula_translator.py) for complete mappings.

## Project Structure

```
RPT-to-RDF/
├── src/
│   ├── extraction/       # RPT → XML extraction
│   ├── parsing/          # Crystal XML parsing
│   ├── transformation/   # Crystal → Oracle conversion
│   ├── generation/       # Oracle XML/RDF generation
│   └── utils/            # Logging, validation, utilities
├── config/               # YAML configuration files
├── docker/rpttoxml/      # Docker-based extraction
├── tools/RptToXmlJava/   # Java extractor source
└── tests/                # Test suite
```

## Requirements

- **Python 3.9+**
- **Docker** (recommended for extraction)
- **Oracle Reports 12c** (optional, for RDF generation)

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Setup and usage guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [TODO.md](TODO.md) - Roadmap and completed features

## Error Codes

Errors use standardized codes (RPT-XXXX) with descriptions and suggested fixes:
- `RPT-1xxx`: Extraction errors
- `RPT-2xxx`: Parsing errors
- `RPT-3xxx`: Formula errors
- `RPT-8xxx`: Generation errors

See [src/utils/error_handler.py](src/utils/error_handler.py) for complete error reference.

## License

MIT License
