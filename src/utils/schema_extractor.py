"""
Schema Extractor for RPT to RDF Converter.

Extracts database schema requirements from Crystal Reports XML files
and generates Oracle DDL scripts for creating the required tables/views.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ColumnDefinition:
    """Definition of a database column."""

    name: str
    crystal_type: str
    oracle_type: str = ""
    nullable: bool = True
    heading_text: str = ""

    def __post_init__(self):
        if not self.oracle_type:
            self.oracle_type = self._map_type(self.crystal_type)

    def _map_type(self, crystal_type: str) -> str:
        """Map Crystal Reports type to Oracle type."""
        type_map = {
            "xsd:long": "NUMBER",
            "xsd:int": "NUMBER",
            "xsd:integer": "NUMBER",
            "xsd:short": "NUMBER",
            "xsd:decimal": "NUMBER(15,2)",
            "xsd:double": "NUMBER",
            "xsd:float": "NUMBER",
            "xsd:string": "VARCHAR2(255)",
            "persistentMemo": "VARCHAR2(4000)",
            "xsd:date": "DATE",
            "xsd:dateTime": "TIMESTAMP",
            "xsd:time": "DATE",
            "xsd:boolean": "VARCHAR2(1)",
            "blob": "BLOB",
        }
        return type_map.get(crystal_type, "VARCHAR2(255)")


@dataclass
class TableDefinition:
    """Definition of a database table/view."""

    name: str
    alias: str
    object_type: str  # "Table" or "View"
    columns: List[ColumnDefinition] = field(default_factory=list)
    source_report: str = ""


@dataclass
class SchemaRequirements:
    """Complete schema requirements extracted from reports."""

    tables: Dict[str, TableDefinition] = field(default_factory=dict)
    reports_analyzed: List[str] = field(default_factory=list)

    def add_table(self, table: TableDefinition) -> None:
        """Add or merge a table definition."""
        if table.name in self.tables:
            # Merge columns (add any new columns)
            existing = self.tables[table.name]
            existing_col_names = {c.name for c in existing.columns}
            for col in table.columns:
                if col.name not in existing_col_names:
                    existing.columns.append(col)
        else:
            self.tables[table.name] = table

    def generate_ddl(self, schema_name: Optional[str] = None) -> str:
        """Generate Oracle DDL for all tables."""
        ddl_parts = []
        prefix = f"{schema_name}." if schema_name else ""

        ddl_parts.append("-- Oracle DDL generated from Crystal Reports")
        ddl_parts.append(f"-- Reports analyzed: {', '.join(self.reports_analyzed)}")
        ddl_parts.append("")

        for table_name, table in sorted(self.tables.items()):
            # Determine if it's likely a view (name starts with vw_ or v_)
            is_view = table_name.lower().startswith(("vw_", "v_"))

            if is_view:
                ddl_parts.append(f"-- View: {table_name}")
                ddl_parts.append(
                    f"-- (Create as table for testing, or as view with appropriate query)"
                )

            ddl_parts.append(f"CREATE TABLE {prefix}{table_name} (")

            col_defs = []
            for col in table.columns:
                null_str = "" if col.nullable else " NOT NULL"
                col_defs.append(f"    {col.name} {col.oracle_type}{null_str}")

            ddl_parts.append(",\n".join(col_defs))
            ddl_parts.append(");")
            ddl_parts.append("")

        return "\n".join(ddl_parts)

    def generate_summary(self) -> str:
        """Generate a summary of schema requirements."""
        lines = []
        lines.append("=" * 60)
        lines.append("SCHEMA REQUIREMENTS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Reports analyzed: {len(self.reports_analyzed)}")
        lines.append(f"Tables/Views required: {len(self.tables)}")
        lines.append("")

        for table_name, table in sorted(self.tables.items()):
            is_view = table_name.lower().startswith(("vw_", "v_"))
            obj_type = "VIEW" if is_view else "TABLE"
            lines.append(f"{obj_type}: {table_name}")
            lines.append(f"  Columns: {len(table.columns)}")
            for col in table.columns:
                lines.append(f"    - {col.name}: {col.oracle_type}")
            lines.append("")

        return "\n".join(lines)


class SchemaExtractor:
    """Extracts schema requirements from Crystal Reports XML files."""

    def extract_from_file(self, xml_path: Path) -> SchemaRequirements:
        """Extract schema from a single Crystal XML file."""
        requirements = SchemaRequirements()

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            report_name = root.get("name", xml_path.stem)
            requirements.reports_analyzed.append(report_name)

            # Find all tables in Database section
            for table_elem in root.findall(".//Database/Tables/Table"):
                table = self._parse_table(table_elem, report_name)
                if table:
                    requirements.add_table(table)

        except ET.ParseError as e:
            print(f"Error parsing {xml_path}: {e}")

        return requirements

    def extract_from_directory(self, xml_dir: Path) -> SchemaRequirements:
        """Extract schema from all Crystal XML files in a directory."""
        requirements = SchemaRequirements()

        for xml_path in xml_dir.glob("*.xml"):
            file_reqs = self.extract_from_file(xml_path)
            requirements.reports_analyzed.extend(file_reqs.reports_analyzed)
            for table in file_reqs.tables.values():
                requirements.add_table(table)

        return requirements

    def _parse_table(self, table_elem: ET.Element, report_name: str) -> Optional[TableDefinition]:
        """Parse a Table element into a TableDefinition."""
        name = table_elem.get("name")
        if not name:
            return None

        table = TableDefinition(
            name=name,
            alias=table_elem.get("alias", name),
            object_type=table_elem.get("type", "Table"),
            source_report=report_name,
        )

        # Parse fields
        for field_elem in table_elem.findall(".//Field"):
            col = ColumnDefinition(
                name=field_elem.get("name", ""),
                crystal_type=field_elem.get("valueType", "xsd:string"),
                heading_text=field_elem.get("headingText", ""),
            )
            if col.name:
                table.columns.append(col)

        return table


def main():
    """CLI for schema extraction."""
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python schema_extractor.py <xml_file_or_directory> [--ddl] [--schema SCHEMA_NAME]"
        )
        sys.exit(1)

    path = Path(sys.argv[1])
    generate_ddl = "--ddl" in sys.argv
    schema_name = None
    if "--schema" in sys.argv:
        idx = sys.argv.index("--schema")
        if idx + 1 < len(sys.argv):
            schema_name = sys.argv[idx + 1]

    extractor = SchemaExtractor()

    if path.is_file():
        requirements = extractor.extract_from_file(path)
    else:
        requirements = extractor.extract_from_directory(path)

    if generate_ddl:
        print(requirements.generate_ddl(schema_name))
    else:
        print(requirements.generate_summary())


if __name__ == "__main__":
    main()
