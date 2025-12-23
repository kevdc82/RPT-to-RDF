# RptToXml Docker Container

This Docker container runs the Crystal Reports Java SDK on Linux to extract RPT files to XML format. This is required for macOS users since the Crystal Reports Java SDK has path resolution issues on macOS.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Crystal Reports SDK JARs** in `tools/RptToXmlJava/lib/`
3. **RptToXml Java project** built (`tools/RptToXmlJava/build.sh`)

## Quick Start

### 1. Build the Docker Image

```bash
cd docker/rpttoxml
./build.sh
```

### 2. Extract a Single RPT File

```bash
./extract-rpt.sh /path/to/report.rpt /path/to/output.xml
```

### 3. Batch Extract Directory

```bash
./extract-rpt.sh --batch ./input ./output
```

## Usage

### Using the Wrapper Script (Recommended)

```bash
# Single file (output defaults to same name with .xml extension)
./extract-rpt.sh report.rpt

# Single file with custom output
./extract-rpt.sh report.rpt custom_output.xml

# Batch convert all RPT files in a directory
./extract-rpt.sh --batch ./input ./output
```

### Using Docker Directly

```bash
# Single file
docker run --rm \
  -v $(pwd)/input:/reports/input:ro \
  -v $(pwd)/output:/reports/output \
  rpttoxml:latest \
  /reports/input/report.rpt /reports/output/report.xml

# Batch convert (recursive)
docker run --rm \
  -v $(pwd)/input:/reports/input:ro \
  -v $(pwd)/output:/reports/output \
  rpttoxml:latest \
  -r /reports/input
```

## Integration with RPT-to-RDF Pipeline

For macOS users, update `config/settings.yaml` to use Docker-based extraction:

```yaml
extraction:
  # Use Docker for RPT extraction on macOS
  use_docker: true
  docker_image: "rpttoxml:latest"

  # Or use native Java on Windows/Linux
  # rpttoxml_path: "./tools/RptToXmlJava/rpttoxml.sh"
```

## Troubleshooting

### "Docker image not found"

Run the build script:
```bash
./build.sh
```

### "Crystal Reports SDK JARs not found"

Ensure the SDK JARs are in `tools/RptToXmlJava/lib/`. Download the Crystal Reports for Eclipse Runtime from SAP.

### "Permission denied"

Ensure Docker has permission to access the mounted directories:
```bash
chmod -R 755 ./input ./output
```

### Container exits immediately

Check Docker logs:
```bash
docker logs $(docker ps -lq)
```

## Technical Details

- **Base Image**: `eclipse-temurin:11-jdk` (OpenJDK 11 on Ubuntu)
- **Crystal Reports SDK**: Crystal Reports for Eclipse Runtime Libraries
- **Package**: `com.crystaldecisions.sdk.occa.report.application.ReportClientDocument`

The container uses the `com.crystaldecisions.sdk` package (not `com.crystaldecisions12.sdk`) which supports opening local RPT files without a Crystal Reports Server connection.

### Important: Path Handling

The Crystal Reports Java SDK has specific requirements for file paths:

1. **Files must be in the same directory as the JAR files** - The SDK resolves paths relative to the JAR location (`/app` in the container)
2. **Use filename only, not full paths** - When opening a report, use just `report.rpt`, not `/path/to/report.rpt`
3. **WEB-INF structure** - The SDK expects JARs in `WEB-INF/lib/` and config in `WEB-INF/classes/`

The wrapper script handles this automatically by mounting each RPT file directly to `/app/`.

### Solution for "Unexpected error determining relative path"

This error occurs when the SDK cannot resolve the report path. The solution involves:

1. Using the correct package (`com.crystaldecisions.sdk`, not `com.crystaldecisions12.sdk`)
2. Setting `ReportClientDocument.inprocConnectionString` for in-process mode
3. Placing reports in the JAR directory (or using symlinks)
4. Using filename-only references

References:
- [SAP Community Discussion](https://community.sap.com/t5/technology-q-a/com-crystaldecisions-sdk-occa-report-lib-reportsdkexception-unexpected/qaq-p/3891331)
- [Blog: ReportSDKException Solution](https://ewithe.blogspot.com/2014/05/reportsdkexception-unexpected-error.html)
- [Koen Aerts: Local .rpt Files](https://koenaerts.ca/use-local-rpt-files-in-crystal-reports-java-api/)
