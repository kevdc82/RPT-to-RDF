# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RPT-to-RDF is a Python batch conversion tool that converts Crystal Reports 14 (.rpt) files to Oracle Reports 12c (.rdf) files. It uses a 5-stage pipeline architecture and is designed for automated batch processing of 200+ reports.

## Common Commands

```bash
# Install dependencies
pip install -e .              # Install package in editable mode
pip install -r requirements.txt  # Install dependencies only

# Run conversion
python -m src.main convert <input> <output>           # Convert files
python -m src.main convert ./input/ ./output/ -w 8    # Batch convert with 8 workers
python -m src.main convert ./input/ ./output/ --dry-run  # Analyze without converting
python -m src.main convert ./input/ ./output/ --mock     # Test without Crystal/Oracle

# Other commands
python -m src.main analyze ./input/       # Analyze report complexity
python -m src.main validate report.rdf    # Validate converted file
python -m src.main check-config           # Check environment setup

# Run tests
pytest                        # Run all tests
pytest tests/test_formula_translator.py   # Run specific test file
pytest -v -k "test_iif"       # Run tests matching pattern
pytest --cov=src              # Run with coverage

# Code formatting
black src/                    # Format code
isort src/                    # Sort imports
mypy src/                     # Type checking
```

## Architecture

### 5-Stage Pipeline (`src/pipeline.py`)

```
[RPT Files] → Extraction → Parsing → Transformation → Generation → [RDF Files]
```

1. **Extraction** (`src/extraction/rpt_extractor.py`): Converts binary RPT to XML using RptToXml (Java or .NET version)
2. **Parsing** (`src/parsing/crystal_parser.py`): Parses Crystal XML into `ReportModel` (defined in `src/parsing/report_model.py`)
3. **Transformation** (`src/transformation/`): Maps Crystal elements to Oracle equivalents
4. **Generation** (`src/generation/oracle_xml_generator.py`): Produces Oracle Reports XML format
5. **Conversion** (`src/generation/rdf_converter.py`): Converts XML to binary RDF using Oracle's rwconverter

### Core Data Model (`src/parsing/report_model.py`)

`ReportModel` is the central data structure bridging Crystal and Oracle formats. It contains:
- `data_sources`, `queries`, `parameters`, `formulas` (data model)
- `sections`, `groups` (layout model)
- `subreports`, `metadata` (references and properties)

### Key Transformers (`src/transformation/`)

- `formula_translator.py`: Converts Crystal formulas to PL/SQL using `FUNCTION_MAP` (40+ function mappings)
- `type_mapper.py`: Maps Crystal data types to Oracle types
- `layout_mapper.py`: Converts Crystal sections to Oracle frames
- `parameter_mapper.py`: Converts report parameters

### Mock Mode

The `--mock` flag uses `MockRptExtractor` and `MockRDFConverter` for testing without Crystal Reports SDK or Oracle installed. Useful for development on macOS/Linux.

## Configuration

Main config: `config/settings.yaml`
- `extraction.rpttoxml_path`: Path to RptToXml (Java: `./tools/RptToXmlJava/rpttoxml.sh` or .NET: `./tools/RptToXml/RptToXml.exe`)
- `oracle.home`: ORACLE_HOME directory
- `oracle.connection`: Database connection string
- `conversion.on_unsupported_formula`: `placeholder` | `skip` | `fail`

Mapping files:
- `config/formula_mappings.yaml`: Crystal to PL/SQL function mappings
- `config/type_mappings.yaml`: Crystal to Oracle type mappings
- `config/connection_templates.yaml`: Database connection templates

## Key Patterns

### Partial Conversion Strategy
The tool converts all possible elements and generates placeholders for unsupported features. Even partial conversions produce runnable RDF files. Check `ConversionReport` for detailed success/failure tracking.

### Formula Reference Syntax
- `{Table.Field}` → `:COLUMN_NAME` (Oracle bind variable)
- `@FormulaName` → `CF_FORMULANAME()` (Oracle function call)
- `?Parameter` → `:P_PARAMETER` (Oracle parameter)

### Error Handling (`src/utils/error_handler.py`)
Errors are categorized by `ErrorCategory` enum and collected in `ConversionReport`, which can generate HTML, CSV, and JSON reports.

## Platform Requirements

- **Full pipeline (extraction + conversion)**: Windows Server with Oracle Reports 12c (for rwconverter)
- **Extraction only**: Any platform with Java 11+ (using RptToXml Java Edition)
- **Development/Testing**: Any platform using `--mock` mode

## RptToXml Extractors

Two versions are available for extracting Crystal Reports structure to XML:

### Java Edition (Recommended - Cross-platform)
Located in `tools/RptToXmlJava/`. Works on Linux, macOS, and Windows.

```bash
cd tools/RptToXmlJava
./build.sh                    # Build the JAR
./rpttoxml.sh report.rpt      # Extract a report
```

Requires: Java 11+, Crystal Reports for Eclipse SDK (JARs in `lib/`)

### .NET Edition (Windows only)
Located in `tools/RptToXml/`. Legacy C# version.

```bash
# On Windows with Visual Studio
cd tools/RptToXml
msbuild RptToXml.sln
```

Requires: Windows, .NET Framework, Crystal Reports SDK

## Setup Scripts

- `tools/RptToXmlJava/build.sh`: Build the Java extractor
- `tools/setup_rpttoxml.ps1`: Windows PowerShell script to clone and build .NET RptToXml
- `tools/setup_rpttoxml.sh`: macOS/Linux script to clone .NET RptToXml repo
