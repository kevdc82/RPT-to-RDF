# RptToXml (Java Edition)

Cross-platform Crystal Reports to XML extractor using the SAP Crystal Reports Java SDK.

## Features

- **Cross-platform**: Works on Windows, Linux, and macOS
- **Comprehensive extraction**: Extracts formulas, parameters, database info, layout, and subreports
- **Batch processing**: Process entire directories recursively
- **Same output format**: Compatible with the .NET RptToXml tool

## Requirements

- **Java 11 or higher** (JDK for building, JRE for running)
- **SAP Crystal Reports for Eclipse Runtime** (included in `lib/` directory)

## Building

### With Maven (recommended)
```bash
./build.sh
```

### Manual build
```bash
./build.sh  # Uses javac if Maven not available
```

## Usage

### Single file
```bash
java -jar target/RptToXml.jar report.rpt
java -jar target/RptToXml.jar report.rpt output.xml
```

### Directory (recursive)
```bash
java -jar target/RptToXml.jar -r ./reports/
```

### Using wrapper script
```bash
./rpttoxml.sh report.rpt
./rpttoxml.sh -r ./reports/
```

## Output Format

The tool extracts report structure to XML with the following elements:

```xml
<CrystalReport name="report.rpt" extractedBy="RptToXml-Java" version="1.0.0">
    <DataDefinition>
        <FormulaFields>...</FormulaFields>
        <ParameterFields>...</ParameterFields>
        <Groups>...</Groups>
        <SortFields>...</SortFields>
        <SummaryFields>...</SummaryFields>
        <RunningTotalFields>...</RunningTotalFields>
    </DataDefinition>
    <Database>
        <Tables>...</Tables>
        <TableLinks>...</TableLinks>
    </Database>
    <ReportDefinition>
        <Areas>
            <Area>
                <Section>
                    <ReportObjects>...</ReportObjects>
                </Section>
            </Area>
        </Areas>
    </ReportDefinition>
    <Subreports>...</Subreports>
</CrystalReport>
```

## Integration with RPT-to-RDF

This tool is used by the RPT-to-RDF converter to extract Crystal Report structure before transformation to Oracle Reports format.

Configure in `config/settings.yaml`:
```yaml
extraction:
  rpttoxml_path: "./tools/RptToXmlJava/rpttoxml.sh"
```

## Crystal Reports SDK

The `lib/` directory contains the SAP Crystal Reports for Eclipse runtime JARs. These are required to read RPT files and are licensed under SAP's runtime license (free for internal use).

**Key JARs:**
- `CrystalReportsRuntime.jar` - Core runtime
- `CrystalCommon2.jar` - Common utilities
- `JDBInterface.jar` - Database interface
- `DatabaseConnectors.jar` - Database connectors
- `XMLConnector.jar` - XML support

## Troubleshooting

### "Could not find or load main class"
Ensure all JARs are in the `lib/` directory and the classpath is set correctly.

### "No CRConfig.xml found"
Copy `CRConfig.xml` from `src/main/resources/` to the current directory when running.

### Font rendering issues on Linux
Install Microsoft TrueType core fonts:
```bash
sudo apt-get install ttf-mscorefonts-installer  # Debian/Ubuntu
```

## License

The RptToXml Java source code is MIT licensed.

The Crystal Reports SDK JARs are proprietary SAP software and subject to SAP's license terms. They are free to use for internal applications but cannot be redistributed for commercial purposes.
