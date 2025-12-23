# RptToXml Docker Image
# Extracts Crystal Reports (.rpt) files to XML format using the Crystal Reports Java SDK
#
# Build:
#   docker build -t rpttoxml:latest .
#
# Usage:
#   docker run -v /path/to/reports:/reports rpttoxml:latest /reports/input.rpt /reports/output.xml
#

FROM eclipse-temurin:11-jdk

LABEL maintainer="RPT-to-RDF Project"
LABEL description="Crystal Reports to XML extractor using Java SDK"

# Install required packages including fonts (important for Crystal Reports)
RUN apt-get update && apt-get install -y \
    fontconfig \
    libfreetype6 \
    fonts-dejavu \
    fonts-liberation \
    software-properties-common \
    && echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y ttf-mscorefonts-installer || true \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy the RptToXml JAR and dependencies
COPY target/RptToXml.jar /app/
COPY lib/ /app/lib/

# Copy CRConfig.xml
COPY CRConfig.xml /app/

# Create directories for reports
RUN mkdir -p /reports/input /reports/output

# The Crystal Reports SDK expects a specific directory structure:
# WEB-INF/lib/ for JARs and WEB-INF/classes/ for CRConfig.xml
# The reportLocation is relative to the JAR location

# Create WEB-INF structure that Crystal Reports SDK expects
RUN mkdir -p /app/WEB-INF/lib /app/WEB-INF/classes && \
    cp /app/lib/*.jar /app/WEB-INF/lib/ && \
    cp /app/RptToXml.jar /app/WEB-INF/lib/

# Create symlinks for reports directory
RUN ln -sf /reports/input /app/input && \
    ln -sf /reports/output /app/output && \
    ln -sf /reports/input /app/WEB-INF/input

# Create CRConfig.xml in WEB-INF/classes (where SDK looks for it)
RUN echo '<?xml version="1.0" encoding="utf-8"?>' > /app/WEB-INF/classes/CRConfig.xml && \
    echo '<CrystalReportEngine-configuration>' >> /app/WEB-INF/classes/CRConfig.xml && \
    echo '    <timeout>0</timeout>' >> /app/WEB-INF/classes/CRConfig.xml && \
    echo '</CrystalReportEngine-configuration>' >> /app/WEB-INF/classes/CRConfig.xml

# Also copy to /app for good measure
RUN cp /app/WEB-INF/classes/CRConfig.xml /app/

# Set classpath - include WEB-INF structure
ENV CLASSPATH="/app/WEB-INF/lib/*:/app/WEB-INF/classes:/app"

# Set working directory
WORKDIR /app

# Default entrypoint using WEB-INF classpath
ENTRYPOINT ["java", "-cp", "/app/WEB-INF/lib/*:/app/WEB-INF/classes:/app", "com.rpttoxml.RptToXml"]

# Default command (show help)
CMD ["--help"]
