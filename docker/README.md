# Oracle Reports 12c Docker Setup

This directory contains Docker configuration for running Oracle Reports 12c with `rwconverter` for RDF file generation.

## Overview

Oracle Reports 12c is required to convert the generated Oracle Reports XML files to binary RDF format using `rwconverter`. This setup uses Docker to avoid a full Oracle installation on your development machine.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Oracle Account** - Required to download Oracle software from [Oracle Software Delivery Cloud](https://edelivery.oracle.com)
3. **~20GB disk space** for images and containers

## Required Oracle Downloads

You'll need to download these from Oracle (requires free Oracle account):

1. **Oracle Server JRE 8** (server-jre-8uXXX-linux-x64.tar.gz)
   - From: https://www.oracle.com/java/technologies/javase-server-jre8-downloads.html

2. **Oracle Fusion Middleware 12c Infrastructure** (fmw_12.2.1.4.0_infrastructure.jar)
   - From: Oracle Software Delivery Cloud
   - Search for "Oracle Fusion Middleware 12c Infrastructure"

3. **Oracle Forms and Reports 12c** (fmw_12.2.1.4.0_fr_linux64.bin)
   - From: Oracle Software Delivery Cloud
   - Search for "Oracle Forms and Reports"

## Quick Start

### Option A: Use Pre-built Community Image (Easier)

There are community-maintained Docker images available:

```bash
# Create Docker network
docker network create oranet

# Start Oracle Database (required for Reports metadata)
docker run -d --name oracle-db \
  --network oranet \
  -p 1521:1521 \
  -e ORACLE_PWD=YourPassword123 \
  container-registry.oracle.com/database/express:21.3.0-xe

# Wait for database to be ready (check logs)
docker logs -f oracle-db

# Then follow Option B for Reports installation
```

### Option B: Build from Scratch

See the detailed instructions below or use one of these community projects:

- [DockerFMWReports12c](https://github.com/japareja/DockerFMWReports12c) - WebLogic + Reports 12c
- [DirkNachbar/Docker](https://github.com/DirkNachbar/Docker) - Forms & Reports 12.2.1.3

## Using rwconverter

Once Oracle Reports is running in Docker, you can convert XML to RDF:

```bash
# Copy XML file to container
docker cp report.xml oracle-reports:/tmp/

# Run rwconverter inside container
docker exec oracle-reports /bin/bash -c "
  cd /u01/oracle/product/12c/bin
  ./rwconverter userid=user/pass@db \
    stype=xmlfile source=/tmp/report.xml \
    dtype=rdffile dest=/tmp/report.rdf \
    batch=yes
"

# Copy RDF back
docker cp oracle-reports:/tmp/report.rdf ./
```

## Integration with RPT-to-RDF

Update your `config/settings.yaml`:

```yaml
oracle:
  # Docker-based Oracle Reports
  home: "/u01/oracle/product/12c"
  connection: "system/YourPassword123@oracle-db:1521/XE"

  # Use Docker for conversion
  use_docker: true
  docker_container: "oracle-reports"
```

## Alternative: Remote Oracle Server

If you have Oracle Reports 12c installed on a remote server (Windows/Linux), you can:

1. Generate XML files locally with this tool
2. Copy XML files to the Oracle server
3. Run rwconverter on the Oracle server
4. Copy RDF files back

This may be simpler than setting up Docker if you already have an Oracle environment.

## Troubleshooting

### Container won't start
- Ensure Docker has enough memory allocated (minimum 4GB)
- Check logs: `docker logs oracle-reports`

### rwconverter not found
- The utility is at: `$ORACLE_HOME/bin/rwconverter`
- Ensure ORACLE_HOME is set correctly in the container

### Database connection errors
- Verify the database container is running
- Check network connectivity between containers
- Ensure listener is started in database container

## Resources

- [Oracle Reports Documentation](https://docs.oracle.com/middleware/12213/formsandreports/index.html)
- [rwconverter Reference](https://docs.oracle.com/middleware/12213/formsandreports/use-reports/pbr_xml004.htm)
- [DockerFMWReports12c GitHub](https://github.com/japareja/DockerFMWReports12c)
