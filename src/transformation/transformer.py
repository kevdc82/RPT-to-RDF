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
