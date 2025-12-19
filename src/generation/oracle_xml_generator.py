"""
Oracle Reports XML Generator for RPT to RDF Converter.

Generates Oracle Reports 12c XML format from transformed report data.
"""

import xml.etree.ElementTree as ET
from typing import Optional
from xml.dom import minidom

from ..transformation.transformer import TransformedReport
from ..transformation.layout_mapper import OracleLayout, OracleFrame, OracleField
from ..transformation.formula_translator import TranslatedFormula
from ..transformation.parameter_mapper import OracleParameter
from ..utils.logger import get_logger


class OracleXMLGenerator:
    """Generates Oracle Reports 12c XML format."""

    # Oracle Reports DTD version
    DTD_VERSION = "12.0.0.0"

    def __init__(self):
        """Initialize the XML generator."""
        self.logger = get_logger("oracle_xml_generator")

    def generate(self, report: TransformedReport) -> str:
        """Generate Oracle Reports XML from transformed report.

        Args:
            report: Transformed report data.

        Returns:
            XML string for Oracle Reports.
        """
        self.logger.info(f"Generating Oracle XML for: {report.name}")

        # Create root report element
        root = ET.Element("report", {
            "name": report.name,
            "DTDVersion": self.DTD_VERSION,
        })

        # Generate data model
        self._generate_data_model(root, report)

        # Generate layout
        if report.layout:
            self._generate_layout(root, report.layout)

        # Generate program units (formulas)
        if report.formulas:
            self._generate_program_units(root, report.formulas)

        # Generate parameter form
        if report.parameters:
            self._generate_parameter_form(root, report.parameters)

        # Convert to string with pretty printing
        xml_string = self._prettify(root)

        self.logger.info(f"Generated XML: {len(xml_string)} bytes")
        return xml_string

    def _generate_data_model(self, root: ET.Element, report: TransformedReport) -> None:
        """Generate the data model section."""
        data = ET.SubElement(root, "data")

        # Generate data sources/queries
        for query in report.queries:
            ds = ET.SubElement(data, "dataSource", {
                "name": query["name"],
                "defaultGroupName": f"G_{query['name']}",
            })

            # Add SQL
            select = ET.SubElement(ds, "select")
            select.text = query.get("sql", "")

        # Generate groups for each query
        for query in report.queries:
            group = ET.SubElement(data, "group", {
                "name": f"G_{query['name']}",
            })

            # Add columns as data items
            for col in query.get("columns", []):
                ET.SubElement(group, "dataItem", {
                    "name": col["name"],
                    "datatype": self._map_datatype(col["data_type"]),
                })

        # Generate parameters
        for param in report.parameters:
            p = ET.SubElement(data, "parameter", {
                "name": param.oracle_name,
                "datatype": self._map_datatype(param.data_type),
            })

            if param.initial_value:
                init = ET.SubElement(p, "initialValue")
                init.text = param.initial_value

        # Generate formula placeholders as data items
        for formula in report.formulas:
            if formula.success:
                ET.SubElement(data, "formula", {
                    "name": formula.oracle_name,
                    "source": f"{formula.oracle_name}formula",
                    "datatype": self._map_datatype(formula.return_type),
                })

    def _generate_layout(self, root: ET.Element, layout: OracleLayout) -> None:
        """Generate the layout section."""
        layout_elem = ET.SubElement(root, "layout", {
            "panelPrintOrder": "acrossDown",
            "direction": "default",
        })

        # Add main section
        section = ET.SubElement(layout_elem, "section", {"name": "main"})

        # Generate frame hierarchy
        if layout.margin_frame:
            self._generate_frame(section, layout.margin_frame)

        if layout.header_frame:
            self._generate_frame(section, layout.header_frame)

        if layout.body_frame:
            self._generate_frame(section, layout.body_frame)

        if layout.trailer_frame:
            self._generate_frame(section, layout.trailer_frame)

    def _generate_frame(self, parent: ET.Element, frame: OracleFrame) -> None:
        """Generate a frame element with its children."""
        # Determine element type
        if frame.frame_type == "repeating":
            frame_elem = ET.SubElement(parent, "repeatingFrame", {
                "name": frame.name,
                "source": frame.source_group or "",
                "x": str(int(frame.x)),
                "y": str(int(frame.y)),
                "width": str(int(frame.width)),
                "height": str(int(frame.height)),
                "verticalElasticity": frame.vertical_elasticity,
                "horizontalElasticity": frame.horizontal_elasticity,
                "printDirection": frame.print_direction,
            })
        else:
            frame_elem = ET.SubElement(parent, "frame", {
                "name": frame.name,
                "x": str(int(frame.x)),
                "y": str(int(frame.y)),
                "width": str(int(frame.width)),
                "height": str(int(frame.height)),
                "verticalElasticity": frame.vertical_elasticity,
                "horizontalElasticity": frame.horizontal_elasticity,
            })

        # Generate fields in frame
        for field in frame.fields:
            self._generate_field(frame_elem, field)

        # Generate child frames
        for child in frame.children:
            self._generate_frame(frame_elem, child)

    def _generate_field(self, parent: ET.Element, field: OracleField) -> None:
        """Generate a field element."""
        attrs = {
            "name": field.name,
            "source": field.source,
            "x": str(int(field.x)),
            "y": str(int(field.y)),
            "width": str(int(field.width)),
            "height": str(int(field.height)),
            "fontName": field.font_name,
            "fontSize": str(field.font_size),
            "fontStyle": field.font_style,
            "horizontalAlignment": field.horizontal_alignment,
            "verticalAlignment": field.vertical_alignment,
        }

        if field.format_mask:
            attrs["formatMask"] = field.format_mask

        if not field.visible:
            attrs["visible"] = "no"

        field_elem = ET.SubElement(parent, "field", attrs)

        # Add format trigger if present
        if field.format_trigger:
            ET.SubElement(field_elem, "formatTrigger").text = field.format_trigger

    def _generate_program_units(
        self,
        root: ET.Element,
        formulas: list[TranslatedFormula],
    ) -> None:
        """Generate program units (PL/SQL functions)."""
        program_units = ET.SubElement(root, "programUnits")

        for formula in formulas:
            if not formula.success:
                continue

            # Create function element
            func = ET.SubElement(program_units, "function", {
                "name": f"{formula.oracle_name}formula",
                "returnType": formula.return_type,
            })

            # Add source code
            source = ET.SubElement(func, "textSource")
            source.text = formula.plsql_code

            # Add comments for placeholders
            if formula.is_placeholder:
                comment = ET.SubElement(func, "comment")
                comment.text = f"TODO: Manual conversion required for {formula.original_name}"

    def _generate_parameter_form(
        self,
        root: ET.Element,
        parameters: list[OracleParameter],
    ) -> None:
        """Generate parameter form section."""
        if not parameters:
            return

        param_form = ET.SubElement(root, "parameterForm")

        for param in parameters:
            field = ET.SubElement(param_form, "parameterField", {
                "name": f"PF_{param.oracle_name}",
                "source": param.oracle_name,
                "width": str(param.width * 6),  # Approximate character to pixel
                "label": param.prompt_text,
            })

            if param.list_of_values:
                lov = ET.SubElement(field, "listOfValues", {
                    "restrictToList": "no",
                })
                lov_query = ET.SubElement(lov, "selectStatement")
                lov_query.text = param.list_of_values

    def _map_datatype(self, oracle_type: str) -> str:
        """Map Oracle type to Oracle Reports datatype attribute."""
        type_lower = oracle_type.lower()

        if "number" in type_lower:
            return "number"
        elif "date" in type_lower or "timestamp" in type_lower:
            return "date"
        elif "clob" in type_lower or "blob" in type_lower:
            return "long"
        else:
            return "character"

    def _prettify(self, element: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(element, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def generate_to_file(self, report: TransformedReport, output_path: str) -> None:
        """Generate Oracle XML and write to file.

        Args:
            report: Transformed report data.
            output_path: Path to write XML file.
        """
        xml_content = self.generate(report)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        self.logger.info(f"Wrote XML to: {output_path}")
