"""
Crystal Reports XML Parser for RPT to RDF Converter.

Parses the XML output from RptToXml and builds the internal ReportModel.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from .report_model import (
    ReportModel,
    DataSource,
    Query,
    QueryColumn,
    Formula,
    Parameter,
    Section,
    Field,
    Group,
    SubreportReference,
    ReportMetadata,
    FontSpec,
    FormatSpec,
    SectionType,
    FormulaSyntax,
    DataType,
    ConnectionType,
)
from ..utils.logger import get_logger
from ..utils.error_handler import ErrorHandler, ErrorCategory


class CrystalParser:
    """Parses Crystal Reports XML to internal ReportModel."""

    # Mapping of Crystal section names to SectionType
    SECTION_TYPE_MAP: Dict[str, SectionType] = {
        "reportheader": SectionType.REPORT_HEADER,
        "pageheader": SectionType.PAGE_HEADER,
        "groupheader": SectionType.GROUP_HEADER,
        "detail": SectionType.DETAIL,
        "groupfooter": SectionType.GROUP_FOOTER,
        "pagefooter": SectionType.PAGE_FOOTER,
        "reportfooter": SectionType.REPORT_FOOTER,
    }

    # Mapping of Crystal data types to DataType
    DATA_TYPE_MAP: Dict[str, DataType] = {
        "string": DataType.STRING,
        "number": DataType.NUMBER,
        "currency": DataType.CURRENCY,
        "date": DataType.DATE,
        "time": DataType.TIME,
        "datetime": DataType.DATETIME,
        "boolean": DataType.BOOLEAN,
        "memo": DataType.MEMO,
        "blob": DataType.BLOB,
        "int": DataType.NUMBER,
        "integer": DataType.NUMBER,
        "double": DataType.NUMBER,
        "decimal": DataType.NUMBER,
        "text": DataType.STRING,
        # XSD types from RptToXml-Java
        "xsd:long": DataType.NUMBER,
        "xsd:int": DataType.NUMBER,
        "xsd:integer": DataType.NUMBER,
        "xsd:double": DataType.NUMBER,
        "xsd:decimal": DataType.NUMBER,
        "xsd:string": DataType.STRING,
        "xsd:date": DataType.DATE,
        "xsd:datetime": DataType.DATETIME,
        "xsd:boolean": DataType.BOOLEAN,
        "persistentmemo": DataType.MEMO,
        "transientmemo": DataType.MEMO,
    }

    # Mapping of connection type strings to ConnectionType
    CONNECTION_TYPE_MAP: Dict[str, ConnectionType] = {
        "odbc": ConnectionType.ODBC,
        "ole db": ConnectionType.OLE_DB,
        "oledb": ConnectionType.OLE_DB,
        "jdbc": ConnectionType.JDBC,
        "native": ConnectionType.NATIVE,
        "oracle": ConnectionType.ORACLE,
        "sql server": ConnectionType.SQL_SERVER,
        "sqlserver": ConnectionType.SQL_SERVER,
    }

    def __init__(self) -> None:
        """Initialize the parser."""
        self.logger = get_logger("crystal_parser")
        self.error_handler = ErrorHandler()

    def parse_file(self, xml_path: Path, rpt_path: Optional[Path] = None) -> ReportModel:
        """Parse a Crystal Reports XML file.

        Args:
            xml_path: Path to the XML file from RptToXml.
            rpt_path: Original RPT file path (for metadata).

        Returns:
            Populated ReportModel.

        Raises:
            ET.ParseError: If XML is invalid.
            FileNotFoundError: If XML file doesn't exist.
        """
        self.logger.info(f"Parsing: {xml_path.name}")
        self.error_handler.clear()

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Create base model
        report_name = root.get("Name", xml_path.stem)
        model = ReportModel(
            name=report_name,
            file_path=rpt_path or xml_path,
        )

        # Parse each section of the XML
        self._parse_metadata(root, model)
        self._parse_data_sources(root, model)
        self._parse_queries(root, model)
        self._parse_formulas(root, model)
        self._parse_parameters(root, model)
        self._parse_groups(root, model)
        self._parse_sections(root, model)
        self._parse_subreports(root, model)

        self.logger.info(
            f"Parsed {model.name}: "
            f"{len(model.formulas)} formulas, "
            f"{len(model.parameters)} parameters, "
            f"{len(model.sections)} sections"
        )

        return model

    def parse_string(self, xml_content: str, report_name: str = "Report") -> ReportModel:
        """Parse Crystal Reports XML from a string.

        Args:
            xml_content: XML content as string.
            report_name: Name for the report.

        Returns:
            Populated ReportModel.
        """
        root = ET.fromstring(xml_content)

        model = ReportModel(
            name=root.get("Name", report_name),
        )

        self._parse_metadata(root, model)
        self._parse_data_sources(root, model)
        self._parse_queries(root, model)
        self._parse_formulas(root, model)
        self._parse_parameters(root, model)
        self._parse_groups(root, model)
        self._parse_sections(root, model)
        self._parse_subreports(root, model)

        return model

    def _parse_metadata(self, root: ET.Element, model: ReportModel) -> None:
        """Parse report metadata."""
        metadata = ReportMetadata()

        # Try various element names for metadata
        meta_elements = ["SummaryInfo", "ReportInfo", "Properties", "Metadata"]
        meta_elem = None
        for name in meta_elements:
            meta_elem = root.find(f".//{name}")
            if meta_elem is not None:
                break

        if meta_elem is not None:
            metadata.title = self._get_text(meta_elem, "Title")
            metadata.author = self._get_text(meta_elem, "Author")
            metadata.subject = self._get_text(meta_elem, "Subject")
            metadata.comments = self._get_text(meta_elem, "Comments")

            keywords = self._get_text(meta_elem, "Keywords")
            if keywords:
                metadata.keywords = [k.strip() for k in keywords.split(",")]

        # Page settings
        page_elem = root.find(".//PageSetup") or root.find(".//PrintOptions")
        if page_elem is not None:
            metadata.paper_size = page_elem.get("PaperSize", "Letter")
            metadata.page_orientation = page_elem.get("Orientation", "Portrait")

            # Margins (may be in twips, need conversion)
            metadata.left_margin = self._parse_margin(page_elem.get("LeftMargin", "720"))
            metadata.right_margin = self._parse_margin(page_elem.get("RightMargin", "720"))
            metadata.top_margin = self._parse_margin(page_elem.get("TopMargin", "720"))
            metadata.bottom_margin = self._parse_margin(page_elem.get("BottomMargin", "720"))

        model.metadata = metadata

    def _parse_data_sources(self, root: ET.Element, model: ReportModel) -> None:
        """Parse database connection information."""
        # Look for database info in various locations
        db_elements = [
            root.find(".//DatabaseInfo"),
            root.find(".//DataSourceConnections"),
            root.find(".//Database"),
        ]

        for db_elem in db_elements:
            if db_elem is None:
                continue

            # Parse connection info
            for conn_elem in db_elem.findall(".//Connection") or [db_elem]:
                ds = DataSource(
                    name=conn_elem.get("Name", "Default"),
                    server=conn_elem.get("Server", ""),
                    database=conn_elem.get("Database", ""),
                    username=conn_elem.get("UserID", ""),
                    connection_string=conn_elem.get("ConnectionString", ""),
                )

                # Determine connection type
                conn_type = conn_elem.get("Type", "").lower()
                ds.connection_type = self.CONNECTION_TYPE_MAP.get(
                    conn_type, ConnectionType.UNKNOWN
                )

                model.data_sources.append(ds)

            # Parse tables
            for table_elem in db_elem.findall(".//Table"):
                table_name = table_elem.get("Name", "")
                if table_name and model.data_sources:
                    model.data_sources[0].tables.append(table_name)

    def _parse_queries(self, root: ET.Element, model: ReportModel) -> None:
        """Parse SQL queries from the report."""
        # Look for SQL in various locations
        sql_elem = root.find(".//Command") or root.find(".//SQL") or root.find(".//Query")

        if sql_elem is not None:
            query = Query(
                name="Q_MAIN",
                sql=sql_elem.text or "",
                is_command=sql_elem.tag == "Command",
            )
            model.queries.append(query)

        # Also check tables for their fields to build query columns
        for table_elem in root.findall(".//Table"):
            # Use alias if available, otherwise use name
            table_name = table_elem.get("alias") or table_elem.get("Name") or table_elem.get("name") or ""

            for field_elem in table_elem.findall(".//Field"):
                field_name = field_elem.get("Name", "") or field_elem.get("name", "")
                # Try both Type and valueType attributes (different XML formats)
                field_type = (field_elem.get("Type") or field_elem.get("valueType") or "String").lower()

                col = QueryColumn(
                    name=field_name,
                    table_name=table_name,
                    data_type=self.DATA_TYPE_MAP.get(field_type, DataType.STRING),
                )

                # Create a default query if none exists
                if not model.queries:
                    model.queries.append(Query(name="Q_1"))

                model.queries[0].columns.append(col)
                if table_name not in model.queries[0].tables:
                    model.queries[0].tables.append(table_name)

    def _parse_formulas(self, root: ET.Element, model: ReportModel) -> None:
        """Parse Crystal Reports formulas."""
        formulas_elem = root.find(".//Formulas") or root.find(".//FormulaFields")

        if formulas_elem is None:
            return

        for formula_elem in formulas_elem.findall(".//Formula") or formulas_elem.findall(".//FormulaField"):
            name = formula_elem.get("Name", "")
            if not name:
                continue

            # Get formula text
            text_elem = formula_elem.find(".//Text") or formula_elem.find(".//Expression")
            expression = ""
            if text_elem is not None and text_elem.text:
                expression = text_elem.text

            # Determine syntax
            syntax_str = formula_elem.get("Syntax", "Crystal").lower()
            syntax = FormulaSyntax.BASIC if "basic" in syntax_str else FormulaSyntax.CRYSTAL

            # Determine return type
            return_type_str = formula_elem.get("Type", "String").lower()
            return_type = self.DATA_TYPE_MAP.get(return_type_str, DataType.STRING)

            formula = Formula(
                name=name,
                syntax=syntax,
                expression=expression,
                return_type=return_type,
            )

            # Extract field references from formula
            formula.referenced_fields = self._extract_field_references(expression)
            formula.referenced_formulas = self._extract_formula_references(expression)
            formula.referenced_parameters = self._extract_parameter_references(expression)

            model.formulas.append(formula)

    def _parse_parameters(self, root: ET.Element, model: ReportModel) -> None:
        """Parse report parameters."""
        params_elem = root.find(".//Parameters") or root.find(".//ParameterFields")

        if params_elem is None:
            return

        for param_elem in params_elem.findall(".//Parameter") or params_elem.findall(".//ParameterField"):
            name = param_elem.get("Name", "")
            if not name:
                continue

            # Determine type
            type_str = param_elem.get("Type", "String").lower()
            data_type = self.DATA_TYPE_MAP.get(type_str, DataType.STRING)

            param = Parameter(
                name=name,
                data_type=data_type,
                prompt_text=param_elem.get("PromptText", name),
                allow_multiple=param_elem.get("AllowMultipleValues", "false").lower() == "true",
                allow_null=param_elem.get("AllowNull", "true").lower() == "true",
            )

            # Default value
            default_elem = param_elem.find(".//DefaultValue")
            if default_elem is not None and default_elem.text:
                param.default_value = default_elem.text

            # List of values
            for value_elem in param_elem.findall(".//Value"):
                if value_elem.text:
                    param.list_of_values.append(value_elem.text)

            model.parameters.append(param)

    def _parse_groups(self, root: ET.Element, model: ReportModel) -> None:
        """Parse grouping information."""
        groups_elem = root.find(".//Groups") or root.find(".//GroupFields")

        if groups_elem is None:
            return

        group_num = 1
        for group_elem in groups_elem.findall(".//Group") or groups_elem.findall(".//GroupField"):
            field_name = group_elem.get("Field", "") or group_elem.get("Name", "")

            group = Group(
                name=f"G_{group_num}",
                field_name=field_name,
                sort_direction=group_elem.get("SortDirection", "ascending").lower(),
                keep_together=group_elem.get("KeepTogether", "false").lower() == "true",
                repeat_header=group_elem.get("RepeatHeader", "true").lower() == "true",
            )

            model.groups.append(group)
            group_num += 1

    def _parse_sections(self, root: ET.Element, model: ReportModel) -> None:
        """Parse report sections and their fields."""
        # First try the ReportDefinition/Areas structure from RptToXml-Java
        areas_elem = root.find(".//Areas")
        if areas_elem is not None:
            for area_elem in areas_elem.findall(".//Area"):
                area_kind = area_elem.get("kind", "").lower()
                for section_elem in area_elem.findall(".//Section"):
                    self._parse_single_section(section_elem, model, area_kind)
            return

        # Fallback to older structure
        sections_elem = root.find(".//Sections") or root.find(".//ReportSections")

        if sections_elem is None:
            # Try to find sections at root level
            for section_elem in root.findall(".//Section"):
                self._parse_single_section(section_elem, model)
            return

        for section_elem in sections_elem.findall(".//Section"):
            self._parse_single_section(section_elem, model)

    def _parse_single_section(self, section_elem: ET.Element, model: ReportModel, area_kind: str = "") -> None:
        """Parse a single section element."""
        section_type_str = section_elem.get("Type", "").lower() or area_kind
        section_type = self.SECTION_TYPE_MAP.get(section_type_str)

        if section_type is None:
            # Try to infer from name
            name = section_elem.get("Name", "").lower()
            for key, stype in self.SECTION_TYPE_MAP.items():
                if key in name:
                    section_type = stype
                    break

        if section_type is None:
            section_type = SectionType.DETAIL

        # Parse height - check both 'Height' and 'height' attributes
        height_str = section_elem.get("Height") or section_elem.get("height", "0")

        section = Section(
            name=section_elem.get("Name", f"Section_{len(model.sections) + 1}"),
            section_type=section_type,
            height=self._parse_dimension(height_str),
            suppress=section_elem.get("Suppress", "false").lower() == "true",
            new_page_before=section_elem.get("NewPageBefore", "false").lower() == "true",
            new_page_after=section_elem.get("NewPageAfter", "false").lower() == "true",
            keep_together=section_elem.get("KeepTogether", "false").lower() == "true",
            background_color=section_elem.get("BackgroundColor"),
        )

        # Parse suppress condition
        suppress_elem = section_elem.find(".//SuppressCondition")
        if suppress_elem is not None and suppress_elem.text:
            section.suppress_condition = suppress_elem.text

        # Parse fields in section - check for both Field and ReportObject elements
        for field_elem in section_elem.findall(".//Field"):
            field = self._parse_field(field_elem)
            section.fields.append(field)

        # Also parse ReportObject elements (from RptToXml-Java)
        report_objects_elem = section_elem.find(".//ReportObjects")
        if report_objects_elem is not None:
            for obj_elem in report_objects_elem.findall(".//ReportObject"):
                field = self._parse_report_object(obj_elem)
                section.fields.append(field)

        model.sections.append(section)

    def _parse_report_object(self, obj_elem: ET.Element) -> Field:
        """Parse a ReportObject element (from RptToXml-Java).

        RptToXml-Java uses attributes: left, top, width, height, dataSource, kind, name
        """
        # Get coordinates (lowercase attributes)
        x = self._parse_dimension(obj_elem.get("left", "0"))
        y = self._parse_dimension(obj_elem.get("top", "0"))
        width = self._parse_dimension(obj_elem.get("width", "100"))
        height = self._parse_dimension(obj_elem.get("height", "20"))

        # Get source - could be from dataSource attribute or Text child element
        source = obj_elem.get("dataSource", "")
        if not source:
            text_elem = obj_elem.find(".//Text")
            if text_elem is not None and text_elem.text:
                source = text_elem.text.strip()

        field = Field(
            name=obj_elem.get("name", ""),
            source=source,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        # Determine source type based on source format
        source_lower = field.source.lower()
        if source_lower.startswith("{@") or source_lower.startswith("@"):
            field.source_type = "formula"
        elif source_lower.startswith("{?") or source_lower.startswith("?"):
            field.source_type = "parameter"
        elif source_lower in ["pagenumber", "totalpages", "printdate", "printtime", "pagenofm"]:
            field.source_type = "special"
        elif field.source.startswith("{") and field.source.endswith("}"):
            # Database field like {tablename.fieldname}
            field.source_type = "database"
        else:
            # Text field or other
            field.source_type = "text"

        # Parse font if available
        font_elem = obj_elem.find(".//Font")
        if font_elem is not None:
            field.font = FontSpec(
                name=font_elem.get("Name", "Arial"),
                size=int(font_elem.get("Size", "10")),
                bold=font_elem.get("Bold", "false").lower() == "true",
                italic=font_elem.get("Italic", "false").lower() == "true",
                underline=font_elem.get("Underline", "false").lower() == "true",
                color=font_elem.get("Color", "#000000"),
            )

        return field

    def _parse_field(self, field_elem: ET.Element) -> Field:
        """Parse a field element."""
        field = Field(
            name=field_elem.get("Name", ""),
            source=field_elem.get("Source", "") or field_elem.get("DataField", ""),
            x=self._parse_dimension(field_elem.get("X", "0")),
            y=self._parse_dimension(field_elem.get("Y", "0")),
            width=self._parse_dimension(field_elem.get("Width", "100")),
            height=self._parse_dimension(field_elem.get("Height", "20")),
        )

        # Determine source type
        source = field.source.lower()
        if source.startswith("@"):
            field.source_type = "formula"
        elif source.startswith("?"):
            field.source_type = "parameter"
        elif source in ["pagenumber", "totalpages", "printdate", "printtime"]:
            field.source_type = "special"
        else:
            field.source_type = "database"

        # Parse font
        font_elem = field_elem.find(".//Font")
        if font_elem is not None:
            field.font = FontSpec(
                name=font_elem.get("Name", "Arial"),
                size=int(font_elem.get("Size", "10")),
                bold=font_elem.get("Bold", "false").lower() == "true",
                italic=font_elem.get("Italic", "false").lower() == "true",
                underline=font_elem.get("Underline", "false").lower() == "true",
                color=font_elem.get("Color", "#000000"),
            )

        # Parse format
        format_elem = field_elem.find(".//Format")
        if format_elem is not None:
            field.format = FormatSpec(
                format_string=format_elem.get("FormatString"),
                horizontal_alignment=format_elem.get("HorizontalAlign", "left").lower(),
                vertical_alignment=format_elem.get("VerticalAlign", "top").lower(),
                suppress_if_zero=format_elem.get("SuppressIfZero", "false").lower() == "true",
                suppress_if_blank=format_elem.get("SuppressIfBlank", "false").lower() == "true",
            )

        # Suppress condition
        suppress_elem = field_elem.find(".//SuppressCondition")
        if suppress_elem is not None and suppress_elem.text:
            field.suppress_condition = suppress_elem.text

        # Background color
        field.background_color = field_elem.get("BackgroundColor")

        return field

    def _parse_subreports(self, root: ET.Element, model: ReportModel) -> None:
        """Parse subreport references."""
        for subreport_elem in root.findall(".//Subreport"):
            subreport = SubreportReference(
                name=subreport_elem.get("Name", ""),
                file_path=subreport_elem.get("FilePath"),
                x=self._parse_dimension(subreport_elem.get("X", "0")),
                y=self._parse_dimension(subreport_elem.get("Y", "0")),
                width=self._parse_dimension(subreport_elem.get("Width", "0")),
                height=self._parse_dimension(subreport_elem.get("Height", "0")),
                on_demand=subreport_elem.get("OnDemand", "false").lower() == "true",
            )

            # Parse links
            for link_elem in subreport_elem.findall(".//Link"):
                parent_field = link_elem.get("ParentField", "")
                subreport_param = link_elem.get("SubreportParameter", "")
                if parent_field and subreport_param:
                    subreport.links.append((parent_field, subreport_param))

            model.subreports.append(subreport)

            # Note as potentially complex
            if len(subreport.links) > 3:
                model.add_conversion_note(
                    f"Subreport '{subreport.name}' has {len(subreport.links)} links - may need manual review"
                )

    # Helper methods

    def _get_text(self, elem: ET.Element, tag: str) -> Optional[str]:
        """Get text content of a child element."""
        child = elem.find(f".//{tag}")
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _parse_dimension(self, value: str) -> float:
        """Parse a dimension value in twips (keep as twips for now).

        Crystal Reports XML uses twips (1/1440 inch).
        We store coordinates as twips in the ReportModel, and convert
        to points/inches later in the layout mapper.
        """
        if not value:
            return 0.0
        try:
            # Return value as twips (no conversion)
            return float(value)
        except ValueError:
            return 0.0

    def _parse_margin(self, value: str) -> float:
        """Parse a margin value (twips to inches)."""
        if not value:
            return 0.5
        try:
            twips = float(value)
            return twips / 1440.0  # 1 inch = 1440 twips
        except ValueError:
            return 0.5

    def _extract_field_references(self, expression: str) -> List[str]:
        """Extract database field references from a formula.

        Crystal uses {Table.Field} syntax.
        """
        pattern = r"\{([^@?}][^}]*)\}"
        matches = re.findall(pattern, expression)
        return list(set(matches))

    def _extract_formula_references(self, expression: str) -> List[str]:
        """Extract formula references from a formula.

        Crystal uses @FormulaName or {@FormulaName} syntax.
        """
        # Pattern for @FormulaName
        pattern1 = r"@(\w+)"
        # Pattern for {@FormulaName}
        pattern2 = r"\{@([^}]+)\}"

        matches = re.findall(pattern1, expression) + re.findall(pattern2, expression)
        return list(set(matches))

    def _extract_parameter_references(self, expression: str) -> List[str]:
        """Extract parameter references from a formula.

        Crystal uses ?ParameterName or {?ParameterName} syntax.
        """
        # Pattern for ?ParamName
        pattern1 = r"\?(\w+)"
        # Pattern for {?ParamName}
        pattern2 = r"\{\?([^}]+)\}"

        matches = re.findall(pattern1, expression) + re.findall(pattern2, expression)
        return list(set(matches))
