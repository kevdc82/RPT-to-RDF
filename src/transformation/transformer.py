"""
Main Transformer for RPT to RDF Converter.

Orchestrates the transformation of Crystal Reports elements to Oracle Reports.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ..parsing.report_model import ReportModel
from .type_mapper import TypeMapper
from .formula_translator import FormulaTranslator, TranslatedFormula
from .layout_mapper import LayoutMapper, OracleLayout
from .parameter_mapper import ParameterMapper, OracleParameter
from .connection_mapper import ConnectionMapper, OracleConnection
from .condition_mapper import ConditionMapper, FormatTrigger
from ..utils.logger import get_logger, StageLogger
from ..utils.error_handler import ErrorHandler, ErrorCategory


@dataclass
class TransformedCrossTab:
    """Transformed cross-tab for Oracle Reports matrix layout."""

    name: str
    oracle_name: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    # Dimension columns
    row_columns: list[str] = field(default_factory=list)
    column_columns: list[str] = field(default_factory=list)

    # Summary definitions
    summary_columns: list[dict] = field(default_factory=list)  # [{name, column, function}]

    # Totals
    show_row_totals: bool = True
    show_column_totals: bool = True
    show_grand_total: bool = True

    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "oracle_name": self.oracle_name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "row_columns": self.row_columns,
            "column_columns": self.column_columns,
            "summary_columns": self.summary_columns,
            "show_row_totals": self.show_row_totals,
            "show_column_totals": self.show_column_totals,
            "show_grand_total": self.show_grand_total,
            "warnings": self.warnings,
        }


@dataclass
class TransformedChart:
    """Transformed chart for Oracle Reports."""

    name: str
    oracle_name: str
    chart_type: str  # bar, line, pie, etc.
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    # Data configuration
    category_column: Optional[str] = None
    value_columns: list[str] = field(default_factory=list)
    group_column: Optional[str] = None

    # Appearance
    title: Optional[str] = None
    legend_position: str = "right"
    is_3d: bool = False

    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "oracle_name": self.oracle_name,
            "chart_type": self.chart_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "category_column": self.category_column,
            "value_columns": self.value_columns,
            "group_column": self.group_column,
            "title": self.title,
            "legend_position": self.legend_position,
            "is_3d": self.is_3d,
            "warnings": self.warnings,
        }


@dataclass
class TransformedSubreport:
    """Transformed subreport reference for Oracle Reports."""

    name: str
    oracle_name: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    # Parameter links: [(parent_column, subreport_param)]
    parameter_links: list[tuple[str, str]] = field(default_factory=list)
    # Converted source file path (if subreport was also converted)
    converted_file: Optional[str] = None
    # Suppress condition (converted to Oracle PL/SQL if applicable)
    suppress_trigger: Optional[str] = None
    on_demand: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "oracle_name": self.oracle_name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parameter_links": self.parameter_links,
            "converted_file": self.converted_file,
            "suppress_trigger": self.suppress_trigger,
            "on_demand": self.on_demand,
            "warnings": self.warnings,
        }


@dataclass
class TransformedReport:
    """Result of transforming a Crystal report to Oracle format."""

    name: str
    original_path: str

    # Transformed elements
    connections: list[OracleConnection] = field(default_factory=list)
    queries: list[dict] = field(default_factory=list)
    parameters: list[OracleParameter] = field(default_factory=list)
    formulas: list[TranslatedFormula] = field(default_factory=list)
    format_triggers: list[FormatTrigger] = field(default_factory=list)
    layout: Optional[OracleLayout] = None
    subreports: list[TransformedSubreport] = field(default_factory=list)
    charts: list[TransformedChart] = field(default_factory=list)
    crosstabs: list[TransformedCrossTab] = field(default_factory=list)

    # Metadata
    success: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    conversion_notes: list[str] = field(default_factory=list)

    # Statistics
    elements_total: int = 0
    elements_converted: int = 0
    elements_with_issues: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "original_path": self.original_path,
            "connections": [c.to_dict() for c in self.connections],
            "queries": self.queries,
            "parameters": [p.to_dict() for p in self.parameters],
            "formulas": [f.to_dict() for f in self.formulas],
            "format_triggers": [ft.to_dict() for ft in self.format_triggers],
            "layout": self.layout.to_dict() if self.layout else None,
            "subreports": [sr.to_dict() for sr in self.subreports],
            "charts": [c.to_dict() for c in self.charts],
            "crosstabs": [ct.to_dict() for ct in self.crosstabs],
            "success": self.success,
            "warnings": self.warnings,
            "errors": self.errors,
            "conversion_notes": self.conversion_notes,
            "statistics": {
                "elements_total": self.elements_total,
                "elements_converted": self.elements_converted,
                "elements_with_issues": self.elements_with_issues,
            },
        }

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.elements_total == 0:
            return 100.0
        return (self.elements_converted / self.elements_total) * 100


class Transformer:
    """Orchestrates transformation of Crystal Reports to Oracle Reports."""

    def __init__(
        self,
        formula_prefix: str = "CF_",
        parameter_prefix: str = "P_",
        field_prefix: str = "F_",
        on_unsupported_formula: str = "placeholder",
        on_complex_layout: str = "simplify",
        connection_templates: Optional[dict] = None,
    ):
        """Initialize the transformer.

        Args:
            formula_prefix: Prefix for Oracle formula names.
            parameter_prefix: Prefix for Oracle parameter names.
            field_prefix: Prefix for Oracle field names.
            on_unsupported_formula: Action for unsupported formulas.
            on_complex_layout: Action for complex layouts.
            connection_templates: Optional connection mapping templates.
        """
        self.formula_prefix = formula_prefix
        self.parameter_prefix = parameter_prefix
        self.field_prefix = field_prefix
        self.on_unsupported_formula = on_unsupported_formula
        self.on_complex_layout = on_complex_layout

        # Initialize sub-transformers
        self.type_mapper = TypeMapper()
        self.formula_translator = FormulaTranslator(
            formula_prefix=formula_prefix,
            on_unsupported=on_unsupported_formula,
        )
        self.layout_mapper = LayoutMapper(
            field_prefix=field_prefix,
        )
        self.parameter_mapper = ParameterMapper(
            parameter_prefix=parameter_prefix,
        )
        self.connection_mapper = ConnectionMapper(
            connection_templates=connection_templates,
        )
        self.condition_mapper = ConditionMapper(
            trigger_prefix="FT_",
        )

        self.logger = get_logger("transformer")
        self.error_handler = ErrorHandler()

    def transform(self, report: ReportModel) -> TransformedReport:
        """Transform a Crystal report model to Oracle format.

        Args:
            report: Parsed Crystal report model.

        Returns:
            Transformed report ready for XML generation.
        """
        self.logger.info(f"Transforming report: {report.name}")
        self.error_handler.clear()

        stage_logger = StageLogger(self.logger)

        result = TransformedReport(
            name=report.name,
            original_path=str(report.file_path),
        )

        # Count total elements
        result.elements_total = (
            len(report.data_sources)
            + len(report.queries)
            + len(report.parameters)
            + len(report.formulas)
            + len(report.sections)
            + len(report.groups)
        )

        try:
            # Stage 1: Transform connections
            stage_logger.start_stage("connections", f"{len(report.data_sources)} sources")
            result.connections = self._transform_connections(report, result)
            stage_logger.end_stage(True)

            # Stage 2: Transform queries
            stage_logger.start_stage("queries", f"{len(report.queries)} queries")
            result.queries = self._transform_queries(report, result)
            stage_logger.end_stage(True)

            # Stage 3: Transform parameters
            stage_logger.start_stage("parameters", f"{len(report.parameters)} parameters")
            result.parameters = self._transform_parameters(report, result)
            stage_logger.end_stage(True)

            # Stage 4: Transform formulas
            stage_logger.start_stage("formulas", f"{len(report.formulas)} formulas")
            result.formulas = self._transform_formulas(report, result)
            stage_logger.end_stage(True)

            # Stage 5: Transform layout
            stage_logger.start_stage("layout", f"{len(report.sections)} sections")
            result.layout, format_triggers = self._transform_layout(report, result)
            result.format_triggers = format_triggers
            stage_logger.end_stage(True)

            # Stage 6: Transform subreports
            if report.subreports:
                stage_logger.start_stage("subreports", f"{len(report.subreports)} subreports")
                result.subreports = self._transform_subreports(report, result)
                stage_logger.end_stage(True)

            # Stage 7: Transform charts
            if report.charts:
                stage_logger.start_stage("charts", f"{len(report.charts)} charts")
                result.charts = self._transform_charts(report, result)
                stage_logger.end_stage(True)

            # Stage 8: Transform cross-tabs
            if report.crosstabs:
                stage_logger.start_stage("crosstabs", f"{len(report.crosstabs)} cross-tabs")
                result.crosstabs = self._transform_crosstabs(report, result)
                stage_logger.end_stage(True)

            # Add conversion notes from original report
            result.conversion_notes.extend(report.conversion_notes)

            # Handle unsupported features
            for feature in report.unsupported_features:
                result.warnings.append(f"Unsupported feature: {feature}")
                result.elements_with_issues += 1

        except Exception as e:
            self.logger.error(f"Transformation failed: {e}")
            result.success = False
            result.errors.append(str(e))

        # Log summary
        self.logger.info(
            f"Transformation complete: {result.elements_converted}/{result.elements_total} elements, "
            f"{result.elements_with_issues} issues"
        )

        return result

    def _transform_connections(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[OracleConnection]:
        """Transform database connections."""
        connections = []

        for source in report.data_sources:
            try:
                conn = self.connection_mapper.map_connection(source)
                connections.append(conn)
                result.elements_converted += 1
            except Exception as e:
                result.warnings.append(f"Connection '{source.name}': {e}")
                result.elements_with_issues += 1

        return connections

    def _transform_queries(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[dict]:
        """Transform SQL queries."""
        queries = []

        for query in report.queries:
            try:
                # If the query has explicit SQL, use it
                sql = query.sql

                # Otherwise, generate SQL from tables and columns
                if not sql and query.columns:
                    # Build SELECT statement
                    select_fields = []
                    for col in query.columns:
                        # Use table.field format if table is known
                        if col.table_name:
                            select_fields.append(f"{col.table_name}.{col.name}")
                        else:
                            select_fields.append(col.name)

                    # Build FROM clause
                    from_clause = ", ".join(query.tables) if query.tables else "DUAL"

                    sql = f"SELECT {', '.join(select_fields)} FROM {from_clause}"

                oracle_query = {
                    "name": query.name,
                    "sql": sql,
                    "columns": [
                        {
                            "name": col.name.upper().replace(" ", "_"),
                            "data_type": self.type_mapper.map_type_string(col.data_type),
                        }
                        for col in query.columns
                    ],
                }
                queries.append(oracle_query)
                result.elements_converted += 1
            except Exception as e:
                result.warnings.append(f"Query '{query.name}': {e}")
                result.elements_with_issues += 1

        return queries

    def _transform_parameters(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[OracleParameter]:
        """Transform report parameters."""
        parameters = []

        for param in report.parameters:
            try:
                oracle_param = self.parameter_mapper.map_parameter(param)
                parameters.append(oracle_param)
                result.elements_converted += 1
            except Exception as e:
                result.warnings.append(f"Parameter '{param.name}': {e}")
                result.elements_with_issues += 1

        return parameters

    def _transform_formulas(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[TranslatedFormula]:
        """Transform Crystal formulas to PL/SQL."""
        formulas = []

        for formula in report.formulas:
            try:
                translated = self.formula_translator.translate(formula)
                formulas.append(translated)

                if translated.success:
                    result.elements_converted += 1
                    if translated.is_placeholder:
                        result.elements_with_issues += 1
                        result.warnings.extend(translated.warnings)
                else:
                    result.elements_with_issues += 1
                    result.warnings.extend(translated.warnings)

            except Exception as e:
                result.warnings.append(f"Formula '{formula.name}': {e}")
                result.elements_with_issues += 1

        return formulas

    def _transform_layout(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> tuple[OracleLayout, list[FormatTrigger]]:
        """Transform report layout and generate format triggers."""
        try:
            # Get page dimensions from metadata
            page_width = 612.0  # 8.5 inches in points
            page_height = 792.0  # 11 inches in points

            if report.metadata.page_orientation.lower() == "landscape":
                page_width, page_height = page_height, page_width

            layout = self.layout_mapper.map_layout(
                sections=report.sections,
                groups=report.groups,
                page_width=page_width,
                page_height=page_height,
                condition_mapper=self.condition_mapper,
            )

            # Collect format triggers from layout mapper
            format_triggers = self.layout_mapper.get_format_triggers()

            # Count converted elements
            result.elements_converted += len(report.sections) + len(report.groups)

            return layout, format_triggers

        except Exception as e:
            result.warnings.append(f"Layout transformation: {e}")
            result.elements_with_issues += len(report.sections) + len(report.groups)
            return OracleLayout(), []  # Return empty layout and no triggers

    def _transform_subreports(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[TransformedSubreport]:
        """Transform subreport references.

        Crystal Reports subreports are embedded reports that appear within
        the parent report. Oracle Reports handles subreports differently,
        using either:
        1. Child queries linked to parent groups
        2. Separate RDF files called via SRW.RUN_REPORT

        This method creates TransformedSubreport objects that can be
        converted to either approach.
        """
        subreports = []

        for sr in report.subreports:
            try:
                # Create Oracle-compatible name
                oracle_name = self._make_oracle_subreport_name(sr.name)

                # Convert parameter links
                param_links = []
                for parent_field, subreport_param in sr.links:
                    # Clean up field names
                    parent_col = parent_field.replace("{", "").replace("}", "")
                    if "." in parent_col:
                        parent_col = parent_col.split(".")[-1]
                    parent_col = parent_col.upper().replace(" ", "_")

                    subreport_col = subreport_param.upper().replace(" ", "_")
                    param_links.append((parent_col, subreport_col))

                # Convert suppress condition if present
                suppress_trigger = None
                warnings = []
                if sr.suppress_condition:
                    try:
                        trigger = self.condition_mapper.convert_condition(
                            sr.suppress_condition,
                            f"SR_SUPPRESS_{oracle_name}",
                            trigger_type="suppress",
                        )
                        suppress_trigger = trigger.name
                        warnings.extend(trigger.warnings)
                    except Exception as e:
                        warnings.append(f"Could not convert suppress condition: {e}")

                transformed = TransformedSubreport(
                    name=sr.name,
                    oracle_name=oracle_name,
                    x=sr.x,
                    y=sr.y,
                    width=sr.width,
                    height=sr.height,
                    parameter_links=param_links,
                    suppress_trigger=suppress_trigger,
                    on_demand=sr.on_demand,
                    warnings=warnings,
                )

                subreports.append(transformed)
                result.elements_converted += 1

                # Add notes about subreport handling
                if sr.on_demand:
                    result.conversion_notes.append(
                        f"Subreport '{sr.name}' is on-demand - consider using SRW.RUN_REPORT"
                    )
                if len(param_links) > 0:
                    result.conversion_notes.append(
                        f"Subreport '{sr.name}' has {len(param_links)} parameter links - "
                        "verify parent-child relationships in Oracle"
                    )

            except Exception as e:
                result.warnings.append(f"Subreport '{sr.name}': {e}")
                result.elements_with_issues += 1

        return subreports

    def _make_oracle_subreport_name(self, name: str) -> str:
        """Create Oracle-compatible subreport name."""
        import re
        # Remove invalid characters
        oracle_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure starts with letter
        if oracle_name and oracle_name[0].isdigit():
            oracle_name = "SR_" + oracle_name
        # Add prefix if not present
        if not oracle_name.upper().startswith("SR_"):
            oracle_name = "SR_" + oracle_name
        return oracle_name.upper()

    def _transform_charts(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[TransformedChart]:
        """Transform chart objects.

        Oracle Reports supports charts through:
        1. Oracle BI Graph bean (OG/BI Graph)
        2. Java bean charts
        3. OLE objects

        This transformation creates Oracle-compatible chart definitions
        that can be implemented using Oracle BI Graph or similar.
        """
        charts = []

        # Chart type mapping (Crystal → Oracle BI Graph types)
        chart_type_map = {
            "bar": "BAR_VERT_CLUST",
            "line": "LINE",
            "pie": "PIE",
            "area": "AREA_VERT_ABS",
            "scatter": "SCATTER",
            "doughnut": "PIE_RING",
            "bubble": "BUBBLE",
            "stock": "STOCK_CANDLE",
            "gauge": "GAUGE",
            "funnel": "FUNNEL",
            "radar": "RADAR",
        }

        for chart in report.charts:
            try:
                # Create Oracle-compatible name
                oracle_name = self._make_oracle_chart_name(chart.name)

                # Map chart type
                oracle_type = chart_type_map.get(
                    chart.chart_type.value,
                    "BAR_VERT_CLUST"  # Default to bar chart
                )

                # Extract value columns from data series
                value_columns = []
                for series in chart.data_series:
                    if series.field_name:
                        # Clean up field name
                        col_name = series.field_name.replace("{", "").replace("}", "")
                        if "." in col_name:
                            col_name = col_name.split(".")[-1]
                        value_columns.append(col_name.upper())

                # Clean category field
                category_col = None
                if chart.category_field:
                    category_col = chart.category_field.replace("{", "").replace("}", "")
                    if "." in category_col:
                        category_col = category_col.split(".")[-1]
                    category_col = category_col.upper()

                # Clean group field
                group_col = None
                if chart.group_field:
                    group_col = chart.group_field.replace("{", "").replace("}", "")
                    if "." in group_col:
                        group_col = group_col.split(".")[-1]
                    group_col = group_col.upper()

                warnings = []

                # Check for 3D (Oracle BI Graph supports 3D differently)
                if chart.is_3d:
                    warnings.append("3D chart style may need manual adjustment in Oracle")

                transformed = TransformedChart(
                    name=chart.name,
                    oracle_name=oracle_name,
                    chart_type=oracle_type,
                    x=chart.x,
                    y=chart.y,
                    width=chart.width,
                    height=chart.height,
                    category_column=category_col,
                    value_columns=value_columns,
                    group_column=group_col,
                    title=chart.title,
                    legend_position=chart.legend_position,
                    is_3d=chart.is_3d,
                    warnings=warnings,
                )

                charts.append(transformed)
                result.elements_converted += 1

                # Add note about chart conversion
                result.conversion_notes.append(
                    f"Chart '{chart.name}' ({chart.chart_type.value}) converted - "
                    "implement using Oracle BI Graph or Java bean"
                )

            except Exception as e:
                result.warnings.append(f"Chart '{chart.name}': {e}")
                result.elements_with_issues += 1

        return charts

    def _make_oracle_chart_name(self, name: str) -> str:
        """Create Oracle-compatible chart name."""
        import re
        # Remove invalid characters
        oracle_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure starts with letter
        if oracle_name and oracle_name[0].isdigit():
            oracle_name = "CH_" + oracle_name
        # Add prefix if not present
        if not oracle_name.upper().startswith("CH_"):
            oracle_name = "CH_" + oracle_name
        return oracle_name.upper()

    def _transform_crosstabs(
        self,
        report: ReportModel,
        result: TransformedReport,
    ) -> list[TransformedCrossTab]:
        """Transform cross-tab objects.

        Oracle Reports uses matrix layouts for cross-tab reports.
        This transformation creates Oracle-compatible cross-tab definitions
        that can be implemented using Oracle Reports matrix layout.
        """
        crosstabs = []

        # Summary function mapping (Crystal → Oracle)
        summary_map = {
            "sum": "SUM",
            "count": "COUNT",
            "avg": "AVG",
            "min": "MIN",
            "max": "MAX",
            "count_distinct": "COUNT(DISTINCT)",
        }

        for ct in report.crosstabs:
            try:
                # Create Oracle-compatible name
                oracle_name = self._make_oracle_crosstab_name(ct.name)

                # Clean up row column names
                row_columns = []
                for field in ct.row_fields:
                    col = field.replace("{", "").replace("}", "")
                    if "." in col:
                        col = col.split(".")[-1]
                    row_columns.append(col.upper())

                # Clean up column column names
                column_columns = []
                for field in ct.column_fields:
                    col = field.replace("{", "").replace("}", "")
                    if "." in col:
                        col = col.split(".")[-1]
                    column_columns.append(col.upper())

                # Transform summary cells
                summary_columns = []
                for cell in ct.summary_cells:
                    col_name = cell.field_name.replace("{", "").replace("}", "")
                    if "." in col_name:
                        col_name = col_name.split(".")[-1]

                    summary_columns.append({
                        "name": cell.name,
                        "column": col_name.upper(),
                        "function": summary_map.get(cell.summary_type, "SUM"),
                        "format": cell.format_string,
                    })

                warnings = [
                    "Cross-tab requires Oracle Reports matrix layout - manual implementation required"
                ]

                transformed = TransformedCrossTab(
                    name=ct.name,
                    oracle_name=oracle_name,
                    x=ct.x,
                    y=ct.y,
                    width=ct.width,
                    height=ct.height,
                    row_columns=row_columns,
                    column_columns=column_columns,
                    summary_columns=summary_columns,
                    show_row_totals=ct.show_row_totals,
                    show_column_totals=ct.show_column_totals,
                    show_grand_total=ct.show_grand_total,
                    warnings=warnings,
                )

                crosstabs.append(transformed)
                result.elements_converted += 1

                # Add note about cross-tab conversion
                result.conversion_notes.append(
                    f"Cross-tab '{ct.name}' with {len(row_columns)} row fields, "
                    f"{len(column_columns)} column fields - implement using matrix layout"
                )

            except Exception as e:
                result.warnings.append(f"Cross-tab '{ct.name}': {e}")
                result.elements_with_issues += 1

        return crosstabs

    def _make_oracle_crosstab_name(self, name: str) -> str:
        """Create Oracle-compatible cross-tab name."""
        import re
        # Remove invalid characters
        oracle_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure starts with letter
        if oracle_name and oracle_name[0].isdigit():
            oracle_name = "CT_" + oracle_name
        # Add prefix if not present
        if not oracle_name.upper().startswith("CT_"):
            oracle_name = "CT_" + oracle_name
        return oracle_name.upper()
