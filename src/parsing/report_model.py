"""
Internal report model for RPT to RDF Converter.

Provides a unified representation of report elements that serves
as the intermediate format between Crystal Reports and Oracle Reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class SectionType(Enum):
    """Types of report sections."""

    REPORT_HEADER = "ReportHeader"
    PAGE_HEADER = "PageHeader"
    GROUP_HEADER = "GroupHeader"
    DETAIL = "Detail"
    GROUP_FOOTER = "GroupFooter"
    PAGE_FOOTER = "PageFooter"
    REPORT_FOOTER = "ReportFooter"


class FormulaSyntax(Enum):
    """Crystal Reports formula syntax types."""

    CRYSTAL = "Crystal"
    BASIC = "Basic"


class DataType(Enum):
    """Data types for report elements."""

    STRING = "String"
    NUMBER = "Number"
    CURRENCY = "Currency"
    DATE = "Date"
    TIME = "Time"
    DATETIME = "DateTime"
    BOOLEAN = "Boolean"
    MEMO = "Memo"
    BLOB = "Blob"
    UNKNOWN = "Unknown"


class ConnectionType(Enum):
    """Database connection types."""

    ODBC = "ODBC"
    OLE_DB = "OLE DB"
    JDBC = "JDBC"
    NATIVE = "Native"
    ORACLE = "Oracle"
    SQL_SERVER = "SQL Server"
    UNKNOWN = "Unknown"


@dataclass
class FontSpec:
    """Font specification for text elements."""

    name: str = "Arial"
    size: int = 10
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    color: str = "#000000"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "strikethrough": self.strikethrough,
            "color": self.color,
        }


@dataclass
class FormatSpec:
    """Format specification for fields."""

    format_string: Optional[str] = None
    horizontal_alignment: str = "left"  # left, center, right
    vertical_alignment: str = "top"  # top, middle, bottom
    can_grow: bool = False
    suppress_if_zero: bool = False
    suppress_if_blank: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format_string": self.format_string,
            "horizontal_alignment": self.horizontal_alignment,
            "vertical_alignment": self.vertical_alignment,
            "can_grow": self.can_grow,
            "suppress_if_zero": self.suppress_if_zero,
            "suppress_if_blank": self.suppress_if_blank,
        }


@dataclass
class QueryColumn:
    """Column definition in a query."""

    name: str
    data_type: DataType = DataType.STRING
    table_name: Optional[str] = None
    alias: Optional[str] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "table_name": self.table_name,
            "alias": self.alias,
            "length": self.length,
            "precision": self.precision,
            "scale": self.scale,
        }


@dataclass
class DataSource:
    """Database connection and source information."""

    name: str
    connection_type: ConnectionType = ConnectionType.UNKNOWN
    connection_string: str = ""
    server: str = ""
    database: str = ""
    username: str = ""
    tables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "connection_type": self.connection_type.value,
            "connection_string": self.connection_string,
            "server": self.server,
            "database": self.database,
            "username": self.username,
            "tables": self.tables,
        }


@dataclass
class Query:
    """SQL query definition."""

    name: str
    sql: str = ""
    tables: list[str] = field(default_factory=list)
    columns: list[QueryColumn] = field(default_factory=list)
    is_command: bool = False  # True if this is a direct SQL command

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "sql": self.sql,
            "tables": self.tables,
            "columns": [c.to_dict() for c in self.columns],
            "is_command": self.is_command,
        }


@dataclass
class Formula:
    """Crystal Reports formula definition."""

    name: str
    syntax: FormulaSyntax = FormulaSyntax.CRYSTAL
    expression: str = ""
    return_type: DataType = DataType.STRING
    referenced_fields: list[str] = field(default_factory=list)
    referenced_formulas: list[str] = field(default_factory=list)
    referenced_parameters: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "syntax": self.syntax.value,
            "expression": self.expression,
            "return_type": self.return_type.value,
            "referenced_fields": self.referenced_fields,
            "referenced_formulas": self.referenced_formulas,
            "referenced_parameters": self.referenced_parameters,
        }


@dataclass
class Parameter:
    """Report parameter definition."""

    name: str
    data_type: DataType = DataType.STRING
    default_value: Optional[Any] = None
    allow_multiple: bool = False
    allow_null: bool = True
    prompt_text: str = ""
    value_type: str = "discrete"  # discrete, range
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    edit_mask: Optional[str] = None
    list_of_values: list[Any] = field(default_factory=list)
    cascading_source: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "default_value": self.default_value,
            "allow_multiple": self.allow_multiple,
            "allow_null": self.allow_null,
            "prompt_text": self.prompt_text,
            "value_type": self.value_type,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "edit_mask": self.edit_mask,
            "list_of_values": self.list_of_values,
            "cascading_source": self.cascading_source,
        }


@dataclass
class Field:
    """Report field definition."""

    name: str
    source: str = ""  # Database field, formula, or parameter name
    source_type: str = "database"  # database, formula, parameter, special
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 20.0
    font: FontSpec = field(default_factory=FontSpec)
    format: FormatSpec = field(default_factory=FormatSpec)
    suppress_condition: Optional[str] = None
    hyperlink: Optional[str] = None
    border_style: Optional[str] = None
    background_color: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "source": self.source,
            "source_type": self.source_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "font": self.font.to_dict(),
            "format": self.format.to_dict(),
            "suppress_condition": self.suppress_condition,
            "hyperlink": self.hyperlink,
            "border_style": self.border_style,
            "background_color": self.background_color,
        }


@dataclass
class Group:
    """Report group definition (for grouping and sorting)."""

    name: str
    field_name: str = ""
    sort_direction: str = "ascending"  # ascending, descending
    keep_together: bool = False
    repeat_header: bool = True
    drill_down_enabled: bool = False
    custom_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "field_name": self.field_name,
            "sort_direction": self.sort_direction,
            "keep_together": self.keep_together,
            "repeat_header": self.repeat_header,
            "drill_down_enabled": self.drill_down_enabled,
            "custom_name": self.custom_name,
        }


@dataclass
class Section:
    """Report section definition."""

    name: str
    section_type: SectionType
    height: float = 0.0
    suppress: bool = False
    suppress_condition: Optional[str] = None
    new_page_before: bool = False
    new_page_after: bool = False
    keep_together: bool = False
    fields: list[Field] = field(default_factory=list)
    background_color: Optional[str] = None
    group_number: Optional[int] = None  # For group headers/footers

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "section_type": self.section_type.value,
            "height": self.height,
            "suppress": self.suppress,
            "suppress_condition": self.suppress_condition,
            "new_page_before": self.new_page_before,
            "new_page_after": self.new_page_after,
            "keep_together": self.keep_together,
            "fields": [f.to_dict() for f in self.fields],
            "background_color": self.background_color,
            "group_number": self.group_number,
        }


@dataclass
class SubreportReference:
    """Reference to a subreport."""

    name: str
    file_path: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    links: list[tuple[str, str]] = field(default_factory=list)  # (parent_field, subreport_param)
    suppress_condition: Optional[str] = None
    on_demand: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "links": self.links,
            "suppress_condition": self.suppress_condition,
            "on_demand": self.on_demand,
        }


@dataclass
class CrossTabCell:
    """A cell definition in a cross-tab report."""

    name: str
    field_name: str  # The field being summarized
    summary_type: str = "sum"  # sum, count, avg, min, max, etc.
    format_string: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "field_name": self.field_name,
            "summary_type": self.summary_type,
            "format_string": self.format_string,
        }


@dataclass
class CrossTab:
    """Cross-tab (pivot table) object in a report."""

    name: str

    # Position and size
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    # Row fields (row headers)
    row_fields: list[str] = field(default_factory=list)

    # Column fields (column headers)
    column_fields: list[str] = field(default_factory=list)

    # Summary cells (the data being aggregated)
    summary_cells: list[CrossTabCell] = field(default_factory=list)

    # Totals
    show_row_totals: bool = True
    show_column_totals: bool = True
    show_grand_total: bool = True

    # Section it belongs to
    section_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "row_fields": self.row_fields,
            "column_fields": self.column_fields,
            "summary_cells": [c.to_dict() for c in self.summary_cells],
            "show_row_totals": self.show_row_totals,
            "show_column_totals": self.show_column_totals,
            "show_grand_total": self.show_grand_total,
            "section_name": self.section_name,
        }


class ChartType(Enum):
    """Types of charts supported."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    DOUGHNUT = "doughnut"
    BUBBLE = "bubble"
    STOCK = "stock"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    RADAR = "radar"
    UNKNOWN = "unknown"


@dataclass
class ChartDataSeries:
    """Data series for a chart."""

    name: str
    field_name: str  # Source field for values
    color: Optional[str] = None
    legend_text: Optional[str] = None
    show_values: bool = False
    value_format: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "field_name": self.field_name,
            "color": self.color,
            "legend_text": self.legend_text,
            "show_values": self.show_values,
            "value_format": self.value_format,
        }


@dataclass
class Chart:
    """Chart or graph object in a report."""

    name: str
    chart_type: ChartType = ChartType.BAR

    # Position and size (in twips typically)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    # Data
    category_field: Optional[str] = None  # X-axis or category labels
    data_series: list[ChartDataSeries] = field(default_factory=list)
    group_field: Optional[str] = None  # For grouped charts

    # Appearance
    title: Optional[str] = None
    subtitle: Optional[str] = None
    legend_position: str = "right"  # top, bottom, left, right, none
    show_legend: bool = True
    show_grid_lines: bool = True

    # 3D settings
    is_3d: bool = False
    depth_percent: int = 100

    # Colors
    background_color: Optional[str] = None
    border_color: Optional[str] = None

    # Section it belongs to
    section_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "chart_type": self.chart_type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "category_field": self.category_field,
            "data_series": [ds.to_dict() for ds in self.data_series],
            "group_field": self.group_field,
            "title": self.title,
            "subtitle": self.subtitle,
            "legend_position": self.legend_position,
            "show_legend": self.show_legend,
            "show_grid_lines": self.show_grid_lines,
            "is_3d": self.is_3d,
            "depth_percent": self.depth_percent,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "section_name": self.section_name,
        }


@dataclass
class ReportMetadata:
    """Report metadata and properties."""

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    comments: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    report_version: Optional[str] = None
    crystal_version: Optional[str] = None

    # Page settings
    paper_size: str = "Letter"
    page_orientation: str = "Portrait"
    left_margin: float = 0.5
    right_margin: float = 0.5
    top_margin: float = 0.5
    bottom_margin: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "keywords": self.keywords,
            "comments": self.comments,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "report_version": self.report_version,
            "crystal_version": self.crystal_version,
            "paper_size": self.paper_size,
            "page_orientation": self.page_orientation,
            "left_margin": self.left_margin,
            "right_margin": self.right_margin,
            "top_margin": self.top_margin,
            "bottom_margin": self.bottom_margin,
        }


@dataclass
class ReportModel:
    """Unified internal representation of a report.

    This is the central data structure that represents a report
    in a format-agnostic way, serving as the bridge between
    Crystal Reports and Oracle Reports.
    """

    name: str
    file_path: Path = field(default_factory=lambda: Path("."))

    # Data Model
    data_sources: list[DataSource] = field(default_factory=list)
    queries: list[Query] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    formulas: list[Formula] = field(default_factory=list)

    # Layout Model
    sections: list[Section] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)

    # Subreports
    subreports: list[SubreportReference] = field(default_factory=list)

    # Charts and graphs
    charts: list[Chart] = field(default_factory=list)

    # Cross-tabs (pivot tables)
    crosstabs: list[CrossTab] = field(default_factory=list)

    # Metadata
    metadata: ReportMetadata = field(default_factory=ReportMetadata)

    # Conversion notes
    conversion_notes: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert entire report model to dictionary."""
        return {
            "name": self.name,
            "file_path": str(self.file_path),
            "data_sources": [ds.to_dict() for ds in self.data_sources],
            "queries": [q.to_dict() for q in self.queries],
            "parameters": [p.to_dict() for p in self.parameters],
            "formulas": [f.to_dict() for f in self.formulas],
            "sections": [s.to_dict() for s in self.sections],
            "groups": [g.to_dict() for g in self.groups],
            "subreports": [sr.to_dict() for sr in self.subreports],
            "charts": [c.to_dict() for c in self.charts],
            "crosstabs": [ct.to_dict() for ct in self.crosstabs],
            "metadata": self.metadata.to_dict(),
            "conversion_notes": self.conversion_notes,
            "unsupported_features": self.unsupported_features,
        }

    def get_all_fields(self) -> list[Field]:
        """Get all fields from all sections."""
        fields = []
        for section in self.sections:
            fields.extend(section.fields)
        return fields

    def get_formula_by_name(self, name: str) -> Optional[Formula]:
        """Get a formula by name."""
        for formula in self.formulas:
            if formula.name == name:
                return formula
        return None

    def get_parameter_by_name(self, name: str) -> Optional[Parameter]:
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_sections_by_type(self, section_type: SectionType) -> list[Section]:
        """Get all sections of a specific type."""
        return [s for s in self.sections if s.section_type == section_type]

    def add_conversion_note(self, note: str) -> None:
        """Add a conversion note."""
        if note not in self.conversion_notes:
            self.conversion_notes.append(note)

    def add_unsupported_feature(self, feature: str) -> None:
        """Mark a feature as unsupported."""
        if feature not in self.unsupported_features:
            self.unsupported_features.append(feature)

    def get_complexity_score(self) -> int:
        """Calculate a complexity score for the report.

        Returns a score from 1-10 indicating conversion complexity.
        """
        score = 1

        # Formula complexity
        if len(self.formulas) > 20:
            score += 2
        elif len(self.formulas) > 5:
            score += 1

        # Subreports add complexity
        score += min(len(self.subreports) * 2, 4)

        # Groups add complexity
        if len(self.groups) > 3:
            score += 2
        elif len(self.groups) > 0:
            score += 1

        # Parameters add some complexity
        if len(self.parameters) > 10:
            score += 1

        return min(score, 10)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ReportModel(name={self.name!r}, "
            f"formulas={len(self.formulas)}, "
            f"parameters={len(self.parameters)}, "
            f"sections={len(self.sections)}, "
            f"groups={len(self.groups)}, "
            f"subreports={len(self.subreports)})"
        )
