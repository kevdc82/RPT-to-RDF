"""
Connection Mapper for RPT to RDF Converter.

Maps Crystal Reports database connections to Oracle connections.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import re

from ..parsing.report_model import DataSource, ConnectionType


@dataclass
class OracleConnection:
    """Oracle database connection definition."""

    name: str
    connect_string: str  # TNS name or Easy Connect string
    username: Optional[str] = None
    # Note: password should not be stored, use wallet or prompt

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "connect_string": self.connect_string,
            "username": self.username,
        }


class ConnectionMapper:
    """Maps Crystal Reports database connections to Oracle connections."""

    # Known connection string patterns and their Oracle equivalents
    CONNECTION_PATTERNS = [
        # SQL Server patterns
        (
            r"Server=([^;]+);.*Database=([^;]+)",
            lambda m: f"//{m.group(1)}/{m.group(2)}",  # Easy Connect format
        ),
        (
            r"Data Source=([^;]+);.*Initial Catalog=([^;]+)",
            lambda m: f"//{m.group(1)}/{m.group(2)}",
        ),
        # Oracle patterns
        (
            r"HOST=([^)]+).*SERVICE_NAME=([^)]+)",
            lambda m: f"//{m.group(1)}/{m.group(2)}",
        ),
        (
            r"Data Source=(\w+)",  # TNS name
            lambda m: m.group(1),
        ),
        # ODBC patterns
        (
            r"DSN=([^;]+)",
            lambda m: m.group(1),  # Use DSN name as placeholder
        ),
    ]

    def __init__(self, connection_templates: Optional[dict] = None):
        """Initialize the connection mapper.

        Args:
            connection_templates: Optional mapping of source connections to Oracle TNS names.
        """
        self.templates = connection_templates or {}

    def map_connection(self, source: DataSource) -> OracleConnection:
        """Map a Crystal data source to Oracle connection.

        Args:
            source: Crystal Reports data source.

        Returns:
            Oracle connection definition.
        """
        # Check for explicit template mapping
        if source.name in self.templates:
            return OracleConnection(
                name=source.name,
                connect_string=self.templates[source.name],
                username=source.username or None,
            )

        # Try to parse connection string
        connect_string = self._parse_connection_string(source)

        return OracleConnection(
            name=source.name,
            connect_string=connect_string,
            username=source.username or None,
        )

    def _parse_connection_string(self, source: DataSource) -> str:
        """Parse and convert connection string to Oracle format."""
        conn_str = source.connection_string

        # Try each pattern
        for pattern, converter in self.CONNECTION_PATTERNS:
            match = re.search(pattern, conn_str, re.IGNORECASE)
            if match:
                return converter(match)

        # If we have server and database, create Easy Connect string
        if source.server and source.database:
            return f"//{source.server}/{source.database}"

        # If we have server only
        if source.server:
            return f"//{source.server}/ORCL"  # Default service name

        # Fallback: use source name as TNS name
        return source.name.upper().replace(" ", "_")

    def map_odbc_to_oracle(
        self,
        odbc_dsn: str,
        mapping: Optional[dict] = None,
    ) -> str:
        """Map an ODBC DSN to Oracle TNS name.

        Args:
            odbc_dsn: ODBC data source name.
            mapping: Optional explicit mappings.

        Returns:
            Oracle TNS name or Easy Connect string.
        """
        if mapping and odbc_dsn in mapping:
            return mapping[odbc_dsn]

        # Default: uppercase and clean the DSN name
        return odbc_dsn.upper().replace(" ", "_").replace("-", "_")

    def generate_tns_entry(
        self,
        name: str,
        host: str,
        port: int = 1521,
        service_name: str = "ORCL",
    ) -> str:
        """Generate a TNS entry for tnsnames.ora.

        Args:
            name: TNS name.
            host: Database host.
            port: Database port.
            service_name: Oracle service name.

        Returns:
            TNS entry string.
        """
        return f"""{name} =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = {host})(PORT = {port}))
    (CONNECT_DATA = (SERVICE_NAME = {service_name}))
  )"""

    def batch_map(self, sources: list[DataSource]) -> list[OracleConnection]:
        """Map multiple data sources.

        Args:
            sources: List of Crystal data sources.

        Returns:
            List of Oracle connections.
        """
        return [self.map_connection(s) for s in sources]
