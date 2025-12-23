"""
MDB Data Extractor for RPT to RDF Converter.

Extracts data from Microsoft Access MDB files and generates:
- Oracle DDL (CREATE TABLE statements)
- Oracle INSERT statements
- SQL*Loader control files and data files
- CSV exports
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from access_parser import AccessParser

    HAS_ACCESS_PARSER = True
except ImportError:
    HAS_ACCESS_PARSER = False


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    python_type: type
    oracle_type: str = ""
    max_length: int = 0
    nullable: bool = True
    sample_values: List[Any] = field(default_factory=list)

    def __post_init__(self):
        if not self.oracle_type:
            self.oracle_type = self._infer_oracle_type()

    def _infer_oracle_type(self) -> str:
        """Infer Oracle type from Python type and sample data."""
        if self.python_type == int:
            return "NUMBER"
        elif self.python_type == float:
            return "NUMBER(15,4)"
        elif self.python_type == bool:
            return "VARCHAR2(1)"
        elif self.python_type in (datetime, date):
            return "DATE"
        elif self.python_type == bytes:
            return "BLOB"
        elif self.python_type == str:
            # Use max_length with some padding
            length = max(self.max_length * 2, 255)
            if length > 4000:
                return "CLOB"
            return f"VARCHAR2({min(length, 4000)})"
        else:
            return "VARCHAR2(4000)"


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    row_count: int = 0
    is_system_table: bool = False


@dataclass
class MDBSchema:
    """Schema information extracted from an MDB file."""

    source_file: str
    tables: Dict[str, TableInfo] = field(default_factory=dict)
    extraction_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_user_tables(self) -> Dict[str, TableInfo]:
        """Get non-system tables only."""
        return {name: table for name, table in self.tables.items() if not table.is_system_table}


class MDBExtractor:
    """Extracts schema and data from Microsoft Access MDB files."""

    # System table prefixes to skip
    SYSTEM_PREFIXES = ("MSys", "USys", "~")

    def __init__(self, mdb_path: Path):
        """Initialize with path to MDB file."""
        if not HAS_ACCESS_PARSER:
            raise ImportError(
                "access-parser library is required. Install with: pip install access-parser"
            )

        self.mdb_path = Path(mdb_path)
        if not self.mdb_path.exists():
            raise FileNotFoundError(f"MDB file not found: {mdb_path}")

        self.db = AccessParser(str(self.mdb_path))
        self._schema: Optional[MDBSchema] = None

    def get_table_names(self, include_system: bool = False) -> List[str]:
        """Get list of table names in the database."""
        tables = list(self.db.catalog.keys())
        if not include_system:
            tables = [t for t in tables if not self._is_system_table(t)]
        return sorted(tables)

    def _is_system_table(self, table_name: str) -> bool:
        """Check if table is a system table."""
        return table_name.startswith(self.SYSTEM_PREFIXES)

    def extract_schema(self, sample_rows: int = 100) -> MDBSchema:
        """Extract schema information from all tables."""
        schema = MDBSchema(source_file=str(self.mdb_path))

        for table_name in self.db.catalog.keys():
            try:
                table_info = self._extract_table_schema(table_name, sample_rows)
                schema.tables[table_name] = table_info
            except Exception as e:
                print(f"Warning: Could not extract schema for {table_name}: {e}")

        self._schema = schema
        return schema

    def _extract_table_schema(self, table_name: str, sample_rows: int = 100) -> TableInfo:
        """Extract schema for a single table."""
        table_data = self.db.parse_table(table_name)

        columns = []
        row_count = 0

        for col_name, values in table_data.items():
            if not row_count:
                row_count = len(values)

            # Analyze column data
            col_info = self._analyze_column(col_name, values[:sample_rows])
            columns.append(col_info)

        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count,
            is_system_table=self._is_system_table(table_name),
        )

    def _analyze_column(self, name: str, values: List[Any]) -> ColumnInfo:
        """Analyze column values to determine type and constraints."""
        non_null_values = [v for v in values if v is not None]

        if not non_null_values:
            return ColumnInfo(
                name=name,
                python_type=str,
                nullable=True,
                max_length=255,
            )

        # Determine type from first non-null value
        sample = non_null_values[0]
        python_type = type(sample)

        # Calculate max length for strings
        max_length = 0
        if python_type == str:
            max_length = max(len(str(v)) for v in non_null_values if v)

        # Check nullability
        nullable = len(non_null_values) < len(values)

        return ColumnInfo(
            name=name,
            python_type=python_type,
            nullable=nullable,
            max_length=max_length,
            sample_values=non_null_values[:5],
        )

    def generate_ddl(
        self,
        schema_name: Optional[str] = None,
        tables: Optional[List[str]] = None,
        include_system: bool = False,
    ) -> str:
        """Generate Oracle DDL for creating tables."""
        if not self._schema:
            self.extract_schema()

        ddl_parts = []
        prefix = f"{schema_name}." if schema_name else ""

        ddl_parts.append("-- Oracle DDL generated from Microsoft Access database")
        ddl_parts.append(f"-- Source: {self.mdb_path.name}")
        ddl_parts.append(f"-- Generated: {datetime.now().isoformat()}")
        ddl_parts.append("")

        target_tables = tables or list(self._schema.tables.keys())

        for table_name in sorted(target_tables):
            if table_name not in self._schema.tables:
                continue

            table = self._schema.tables[table_name]
            if table.is_system_table and not include_system:
                continue

            # Sanitize table name for Oracle
            oracle_table_name = self._sanitize_identifier(table_name)

            ddl_parts.append(f"-- Table: {table_name} ({table.row_count} rows)")
            ddl_parts.append(f"CREATE TABLE {prefix}{oracle_table_name} (")

            col_defs = []
            for col in table.columns:
                oracle_col_name = self._sanitize_identifier(col.name)
                null_str = "" if col.nullable else " NOT NULL"
                col_defs.append(f"    {oracle_col_name} {col.oracle_type}{null_str}")

            ddl_parts.append(",\n".join(col_defs))
            ddl_parts.append(");")
            ddl_parts.append("")

        return "\n".join(ddl_parts)

    def generate_inserts(
        self,
        table_name: str,
        schema_name: Optional[str] = None,
        batch_size: int = 1000,
    ) -> str:
        """Generate Oracle INSERT statements for a table."""
        table_data = self.db.parse_table(table_name)

        if not table_data:
            return f"-- No data in table {table_name}"

        columns = list(table_data.keys())
        row_count = len(table_data[columns[0]]) if columns else 0

        prefix = f"{schema_name}." if schema_name else ""
        oracle_table_name = self._sanitize_identifier(table_name)
        oracle_columns = [self._sanitize_identifier(c) for c in columns]

        lines = []
        lines.append(f"-- INSERT statements for {table_name}")
        lines.append(f"-- Rows: {row_count}")
        lines.append("")

        for i in range(row_count):
            row = {col: table_data[col][i] for col in columns}
            values = [self._format_oracle_value(row[col]) for col in columns]

            lines.append(
                f"INSERT INTO {prefix}{oracle_table_name} "
                f"({', '.join(oracle_columns)}) VALUES ({', '.join(values)});"
            )

            # Add commit every batch_size rows
            if (i + 1) % batch_size == 0:
                lines.append("COMMIT;")
                lines.append("")

        lines.append("COMMIT;")
        return "\n".join(lines)

    def export_csv(
        self,
        table_name: str,
        output_path: Path,
        include_header: bool = True,
    ) -> int:
        """Export table data to CSV file."""
        table_data = self.db.parse_table(table_name)

        if not table_data:
            return 0

        columns = list(table_data.keys())
        row_count = len(table_data[columns[0]]) if columns else 0

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if include_header:
                writer.writerow(columns)

            for i in range(row_count):
                row = [self._format_csv_value(table_data[col][i]) for col in columns]
                writer.writerow(row)

        return row_count

    def generate_sqlldr_control(
        self,
        table_name: str,
        schema_name: Optional[str] = None,
        data_file: Optional[str] = None,
    ) -> str:
        """Generate SQL*Loader control file for a table."""
        if not self._schema:
            self.extract_schema()

        if table_name not in self._schema.tables:
            raise ValueError(f"Table {table_name} not found in schema")

        table = self._schema.tables[table_name]
        prefix = f"{schema_name}." if schema_name else ""
        oracle_table_name = self._sanitize_identifier(table_name)
        data_filename = data_file or f"{table_name}.csv"

        lines = []
        lines.append(f"-- SQL*Loader control file for {table_name}")
        lines.append(f"LOAD DATA")
        lines.append(f"INFILE '{data_filename}'")
        lines.append(f"INTO TABLE {prefix}{oracle_table_name}")
        lines.append(f"FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"'")
        lines.append(f"TRAILING NULLCOLS")
        lines.append(f"(")

        col_specs = []
        for col in table.columns:
            oracle_col_name = self._sanitize_identifier(col.name)

            # Add type-specific formatting
            if "DATE" in col.oracle_type:
                col_specs.append(f'    {oracle_col_name} DATE "YYYY-MM-DD HH24:MI:SS"')
            elif "CLOB" in col.oracle_type or "BLOB" in col.oracle_type:
                col_specs.append(f"    {oracle_col_name} CHAR(1000000)")
            else:
                col_specs.append(f"    {oracle_col_name}")

        lines.append(",\n".join(col_specs))
        lines.append(f")")

        return "\n".join(lines)

    def _sanitize_identifier(self, name: str) -> str:
        """Sanitize identifier for Oracle (uppercase, no special chars)."""
        # Replace spaces and special characters
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = "C_" + sanitized
        # Oracle identifiers are uppercase by default
        return sanitized.upper()

    def _format_oracle_value(self, value: Any) -> str:
        """Format a value for Oracle INSERT statement."""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "'Y'" if value else "'N'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (datetime, date)):
            if isinstance(value, datetime):
                return f"TO_TIMESTAMP('{value.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')"
            else:
                return f"TO_DATE('{value.strftime('%Y-%m-%d')}', 'YYYY-MM-DD')"
        elif isinstance(value, bytes):
            # BLOB data - convert to hex
            return f"HEXTORAW('{value.hex()}')"
        else:
            # Escape single quotes
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def _format_csv_value(self, value: Any) -> str:
        """Format a value for CSV export."""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "Y" if value else "N"
        elif isinstance(value, (datetime, date)):
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return value.strftime("%Y-%m-%d")
        elif isinstance(value, bytes):
            return value.hex()
        else:
            return str(value)

    def generate_summary(self) -> str:
        """Generate a summary of the MDB database."""
        if not self._schema:
            self.extract_schema()

        user_tables = self._schema.get_user_tables()

        lines = []
        lines.append("=" * 60)
        lines.append("MDB DATABASE SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Source: {self.mdb_path.name}")
        lines.append(f"Total tables: {len(self._schema.tables)}")
        lines.append(f"User tables: {len(user_tables)}")
        lines.append("")

        # List tables with row counts
        lines.append("USER TABLES:")
        lines.append("-" * 40)

        total_rows = 0
        for name, table in sorted(user_tables.items()):
            lines.append(f"  {name}: {table.row_count} rows, {len(table.columns)} columns")
            total_rows += table.row_count

        lines.append("")
        lines.append(f"Total rows: {total_rows:,}")

        return "\n".join(lines)


def main():
    """CLI for MDB extraction."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mdb_extractor.py <mdb_file> [options]")
        print("Options:")
        print("  --summary           Show database summary")
        print("  --ddl               Generate Oracle DDL")
        print("  --schema NAME       Schema prefix for DDL/inserts")
        print("  --inserts TABLE     Generate INSERT statements for table")
        print("  --csv TABLE         Export table to CSV")
        print("  --sqlldr TABLE      Generate SQL*Loader control file")
        print("  --all-inserts       Generate INSERTs for all tables")
        print("  --all-csv           Export all tables to CSV")
        sys.exit(1)

    mdb_path = Path(sys.argv[1])
    args = sys.argv[2:]

    try:
        extractor = MDBExtractor(mdb_path)
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    schema_name = None
    if "--schema" in args:
        idx = args.index("--schema")
        if idx + 1 < len(args):
            schema_name = args[idx + 1]

    if "--summary" in args or len(args) == 0:
        print(extractor.generate_summary())

    if "--ddl" in args:
        print(extractor.generate_ddl(schema_name=schema_name))

    if "--inserts" in args:
        idx = args.index("--inserts")
        if idx + 1 < len(args):
            table_name = args[idx + 1]
            print(extractor.generate_inserts(table_name, schema_name=schema_name))

    if "--csv" in args:
        idx = args.index("--csv")
        if idx + 1 < len(args):
            table_name = args[idx + 1]
            output_path = Path(f"{table_name}.csv")
            rows = extractor.export_csv(table_name, output_path)
            print(f"Exported {rows} rows to {output_path}")

    if "--sqlldr" in args:
        idx = args.index("--sqlldr")
        if idx + 1 < len(args):
            table_name = args[idx + 1]
            print(extractor.generate_sqlldr_control(table_name, schema_name=schema_name))

    if "--all-inserts" in args:
        extractor.extract_schema()
        for table_name in extractor.get_table_names():
            print(f"\n-- ========== {table_name} ==========")
            print(extractor.generate_inserts(table_name, schema_name=schema_name))

    if "--all-csv" in args:
        extractor.extract_schema()
        output_dir = Path("csv_export")
        output_dir.mkdir(exist_ok=True)
        for table_name in extractor.get_table_names():
            output_path = output_dir / f"{table_name}.csv"
            rows = extractor.export_csv(table_name, output_path)
            print(f"Exported {table_name}: {rows} rows -> {output_path}")


if __name__ == "__main__":
    main()
