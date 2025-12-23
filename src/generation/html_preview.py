"""
HTML Preview Generator for RPT to RDF Converter.

Generates HTML preview of converted reports for visual verification.
"""

from pathlib import Path
from typing import Optional
from html import escape

from ..parsing.report_model import (
    ReportModel,
    Section,
    Field,
    SectionType,
)
from ..utils.logger import get_logger


class HTMLPreviewGenerator:
    """Generates HTML preview of converted reports."""

    def __init__(self):
        """Initialize the HTML preview generator."""
        self.logger = get_logger("html_preview")

    def generate(self, report: ReportModel, output_path: Path) -> None:
        """Generate HTML preview file.

        Args:
            report: Report model to preview.
            output_path: Path to write HTML file.
        """
        self.logger.info(f"Generating HTML preview for: {report.name}")

        html_content = self._generate_html(report)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        self.logger.info(f"Preview written to: {output_path}")

    def _generate_html(self, report: ReportModel) -> str:
        """Generate complete HTML document.

        Args:
            report: Report model to preview.

        Returns:
            HTML string.
        """
        # Calculate page dimensions
        page_width = 612.0  # 8.5 inches in points (72 points/inch)
        page_height = 792.0  # 11 inches in points

        if report.metadata.page_orientation.lower() == "landscape":
            page_width, page_height = page_height, page_width

        # Apply margins
        content_width = page_width - (
            report.metadata.left_margin + report.metadata.right_margin
        ) * 72
        content_height = page_height - (
            report.metadata.top_margin + report.metadata.bottom_margin
        ) * 72

        # Build HTML sections
        sections_html = []

        # Render each section
        for section in report.sections:
            section_html = self._render_section(section, content_width)
            if section_html:
                sections_html.append(section_html)

        # Generate metadata info
        metadata_html = self._render_metadata(report)

        # Generate warnings if any
        warnings_html = ""
        if report.conversion_notes or report.unsupported_features:
            warnings_html = self._render_warnings(report)

        # Build complete document
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(report.name)} - Preview</title>
    <style>
        {self._generate_css(page_width, page_height, content_width)}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="preview-header">
            <h1>Report Preview: {escape(report.name)}</h1>
            {metadata_html}
        </div>

        {warnings_html}

        <div class="report-page" style="width: {page_width}px; height: {page_height}px;">
            <div class="report-content" style="width: {content_width}px; height: {content_height}px;">
                {''.join(sections_html)}
            </div>
        </div>

        <div class="preview-footer">
            <p>This is a preview of the converted report layout. Actual data values are not shown.</p>
            <p>Field positions, fonts, and styling are approximate.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _render_section(self, section: Section, content_width: float) -> str:
        """Render a report section as HTML.

        Args:
            section: Section to render.
            content_width: Width of content area.

        Returns:
            HTML string for the section.
        """
        if section.suppress:
            return ""

        # Determine section class and label
        section_classes = ["section", f"section-{section.section_type.value.lower()}"]
        section_label = section.section_type.value.replace("_", " ").title()

        if section.group_number is not None:
            section_label += f" {section.group_number}"

        # Render fields
        fields_html = []
        for field in section.fields:
            field_html = self._render_field(field)
            if field_html:
                fields_html.append(field_html)

        # Background color
        bg_style = ""
        if section.background_color:
            bg_style = f"background-color: {section.background_color};"

        section_html = f"""
        <div class="{' '.join(section_classes)}"
             style="height: {section.height}px; width: {content_width}px; {bg_style}">
            <div class="section-label">{escape(section_label)}</div>
            <div class="section-content">
                {''.join(fields_html)}
            </div>
        </div>
        """

        return section_html

    def _render_field(self, field: Field) -> str:
        """Render a field as HTML element.

        Args:
            field: Field to render.

        Returns:
            HTML string for the field.
        """
        # Build style attributes
        styles = [
            f"left: {field.x}px",
            f"top: {field.y}px",
            f"width: {field.width}px",
            f"height: {field.height}px",
            f"font-family: {field.font.name}",
            f"font-size: {field.font.size}px",
            f"color: {field.font.color}",
            f"text-align: {field.format.horizontal_alignment}",
        ]

        # Font styles
        font_weight = "bold" if field.font.bold else "normal"
        font_style = "italic" if field.font.italic else "normal"
        styles.append(f"font-weight: {font_weight}")
        styles.append(f"font-style: {font_style}")

        if field.font.underline:
            styles.append("text-decoration: underline")

        # Background color
        if field.background_color:
            styles.append(f"background-color: {field.background_color}")

        # Border style
        if field.border_style:
            styles.append(f"border: 1px solid #000")

        # Vertical alignment
        v_align_map = {
            "top": "flex-start",
            "middle": "center",
            "bottom": "flex-end",
        }
        v_align = v_align_map.get(field.format.vertical_alignment, "flex-start")
        styles.append(f"align-items: {v_align}")

        # Display value based on source type
        display_value = self._get_field_display_value(field)

        field_html = f"""
        <div class="field field-{field.source_type}"
             style="{'; '.join(styles)}"
             title="{escape(field.source)}">
            {escape(display_value)}
        </div>
        """

        return field_html

    def _get_field_display_value(self, field: Field) -> str:
        """Get display value for a field.

        Args:
            field: Field to get display value for.

        Returns:
            Display string.
        """
        if field.source_type == "database":
            # Show column name in curly braces
            return f"{{{field.source}}}"
        elif field.source_type == "formula":
            # Show formula name
            return f"@{field.source}"
        elif field.source_type == "parameter":
            # Show parameter name
            return f"?{field.source}"
        elif field.source_type == "special":
            # Show special field type
            return f"{field.source}"
        else:
            # Text field or unknown
            return field.name if field.name else field.source

    def _render_metadata(self, report: ReportModel) -> str:
        """Render report metadata section.

        Args:
            report: Report model.

        Returns:
            HTML string.
        """
        metadata = report.metadata

        metadata_items = [
            f"<strong>Paper Size:</strong> {metadata.paper_size}",
            f"<strong>Orientation:</strong> {metadata.page_orientation}",
            f"<strong>Margins:</strong> L:{metadata.left_margin}\" R:{metadata.right_margin}\" "
            f"T:{metadata.top_margin}\" B:{metadata.bottom_margin}\"",
        ]

        if metadata.title:
            metadata_items.insert(0, f"<strong>Title:</strong> {escape(metadata.title)}")

        if metadata.author:
            metadata_items.append(f"<strong>Author:</strong> {escape(metadata.author)}")

        # Add complexity score
        complexity = report.get_complexity_score()
        complexity_color = "green" if complexity <= 3 else "orange" if complexity <= 6 else "red"
        metadata_items.append(
            f"<strong>Complexity Score:</strong> "
            f"<span style='color: {complexity_color}'>{complexity}/10</span>"
        )

        # Add counts
        metadata_items.append(f"<strong>Sections:</strong> {len(report.sections)}")
        metadata_items.append(f"<strong>Fields:</strong> {len(report.get_all_fields())}")
        metadata_items.append(f"<strong>Formulas:</strong> {len(report.formulas)}")
        metadata_items.append(f"<strong>Parameters:</strong> {len(report.parameters)}")
        metadata_items.append(f"<strong>Groups:</strong> {len(report.groups)}")

        return f"""
        <div class="metadata">
            {' | '.join(metadata_items)}
        </div>
        """

    def _render_warnings(self, report: ReportModel) -> str:
        """Render warnings and conversion notes.

        Args:
            report: Report model.

        Returns:
            HTML string.
        """
        items = []

        if report.unsupported_features:
            items.append("<div class='warning-section'>")
            items.append("<h3>Unsupported Features</h3>")
            items.append("<ul>")
            for feature in report.unsupported_features:
                items.append(f"<li>{escape(feature)}</li>")
            items.append("</ul>")
            items.append("</div>")

        if report.conversion_notes:
            items.append("<div class='notes-section'>")
            items.append("<h3>Conversion Notes</h3>")
            items.append("<ul>")
            for note in report.conversion_notes:
                items.append(f"<li>{escape(note)}</li>")
            items.append("</ul>")
            items.append("</div>")

        if items:
            return f"""
            <div class="warnings">
                {''.join(items)}
            </div>
            """
        return ""

    def _generate_css(
        self,
        page_width: float,
        page_height: float,
        content_width: float,
    ) -> str:
        """Generate CSS for report styling.

        Args:
            page_width: Width of page in pixels.
            page_height: Height of page in pixels.
            content_width: Width of content area in pixels.

        Returns:
            CSS string.
        """
        css = f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }}

        .preview-container {{
            max-width: {page_width + 100}px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .preview-header {{
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #333;
        }}

        .preview-header h1 {{
            font-size: 24px;
            color: #333;
            margin-bottom: 10px;
        }}

        .metadata {{
            font-size: 12px;
            color: #666;
            line-height: 1.6;
        }}

        .warnings {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }}

        .warnings h3 {{
            font-size: 14px;
            color: #856404;
            margin-bottom: 8px;
        }}

        .warnings ul {{
            margin-left: 20px;
            font-size: 12px;
            color: #856404;
        }}

        .warnings li {{
            margin-bottom: 4px;
        }}

        .warning-section {{
            margin-bottom: 15px;
        }}

        .notes-section {{
            margin-bottom: 15px;
        }}

        .report-page {{
            margin: 20px auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            position: relative;
            border: 1px solid #ccc;
        }}

        .report-content {{
            margin: 0 auto;
            position: relative;
            background-color: white;
        }}

        .section {{
            position: relative;
            border-bottom: 1px dashed #ccc;
            overflow: visible;
        }}

        .section-label {{
            position: absolute;
            left: -120px;
            top: 5px;
            width: 110px;
            font-size: 11px;
            color: #999;
            text-align: right;
            font-weight: bold;
        }}

        .section-content {{
            position: relative;
            width: 100%;
            height: 100%;
        }}

        .section-reportheader {{
            background-color: #f8f9fa;
        }}

        .section-pageheader {{
            background-color: #e9ecef;
            font-weight: bold;
        }}

        .section-groupheader {{
            background-color: #dee2e6;
        }}

        .section-detail {{
            background-color: white;
        }}

        .section-groupfooter {{
            background-color: #dee2e6;
        }}

        .section-pagefooter {{
            background-color: #e9ecef;
        }}

        .section-reportfooter {{
            background-color: #f8f9fa;
        }}

        .field {{
            position: absolute;
            display: flex;
            overflow: hidden;
            white-space: nowrap;
            padding: 2px 4px;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}

        .field:hover {{
            border: 1px solid #007bff;
            background-color: rgba(0, 123, 255, 0.1);
            z-index: 10;
        }}

        .field-database {{
            color: #0066cc;
        }}

        .field-formula {{
            color: #cc6600;
        }}

        .field-parameter {{
            color: #009900;
        }}

        .field-special {{
            color: #666666;
            font-style: italic;
        }}

        .preview-footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
        }}

        .preview-footer p {{
            margin-bottom: 5px;
        }}

        @media print {{
            body {{
                background-color: white;
                padding: 0;
            }}

            .preview-container {{
                box-shadow: none;
                border-radius: 0;
            }}

            .preview-header,
            .preview-footer,
            .warnings {{
                display: none;
            }}

            .section-label {{
                display: none;
            }}

            .report-page {{
                box-shadow: none;
                border: none;
                margin: 0;
            }}
        }}
        """
        return css

    def generate_from_xml(self, xml_path: Path, output_path: Path) -> None:
        """Generate HTML preview from Oracle XML file.

        This is a simplified preview that parses the Oracle XML
        and shows the layout structure.

        Args:
            xml_path: Path to Oracle XML file.
            output_path: Path to write HTML file.
        """
        self.logger.info(f"Generating preview from XML: {xml_path}")

        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            report_name = root.get("name", "Unnamed Report")

            # Extract layout information
            layout_elem = root.find("layout")
            if layout_elem is None:
                self.logger.warning("No layout section found in XML")
                html_content = self._generate_minimal_html(report_name, "No layout information found in XML")
            else:
                html_content = self._generate_xml_preview_html(report_name, layout_elem)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding="utf-8")

            self.logger.info(f"Preview written to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate preview from XML: {e}")
            raise

    def _generate_minimal_html(self, report_name: str, message: str) -> str:
        """Generate minimal HTML for error cases.

        Args:
            report_name: Name of report.
            message: Message to display.

        Returns:
            HTML string.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{escape(report_name)} - Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{escape(report_name)}</h1>
        <p>{escape(message)}</p>
    </div>
</body>
</html>
"""

    def _generate_xml_preview_html(self, report_name: str, layout_elem) -> str:
        """Generate HTML preview from XML layout element.

        Args:
            report_name: Name of report.
            layout_elem: XML layout element.

        Returns:
            HTML string.
        """
        # This is a simplified version - just show structure
        sections_html = []

        for section in layout_elem.findall(".//section"):
            section_name = section.get("name", "unknown")
            sections_html.append(f"<h3>Section: {escape(section_name)}</h3>")

            # Show frames
            for frame in section.findall(".//frame") + section.findall(".//repeatingFrame"):
                frame_name = frame.get("name", "unknown")
                frame_type = frame.tag
                width = frame.get("width", "?")
                height = frame.get("height", "?")

                sections_html.append(
                    f"<div class='frame-info'>"
                    f"<strong>{escape(frame_type)}:</strong> {escape(frame_name)} "
                    f"({width}x{height})"
                    f"</div>"
                )

                # Show fields
                for field in frame.findall(".//field"):
                    field_name = field.get("name", "unknown")
                    field_source = field.get("source", "")
                    sections_html.append(
                        f"<div class='field-info'>Field: {escape(field_name)} "
                        f"({escape(field_source)})</div>"
                    )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{escape(report_name)} - XML Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        h3 {{ color: #555; margin-top: 20px; margin-bottom: 10px; }}
        .frame-info {{ padding: 8px; margin: 5px 0; background: #e9ecef; border-left: 3px solid #007bff; }}
        .field-info {{ padding: 5px 15px; margin: 3px 0 3px 20px; background: #f8f9fa; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Oracle XML Preview: {escape(report_name)}</h1>
        <p style="color: #666; margin-bottom: 20px;">
            This is a structural preview of the Oracle Reports XML layout.
        </p>
        {''.join(sections_html)}
    </div>
</body>
</html>
"""
        return html
