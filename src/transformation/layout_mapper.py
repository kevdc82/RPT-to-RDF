"""
Layout Mapper for RPT to RDF Converter.

Maps Crystal Reports sections and layout to Oracle Reports frames and fields.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ..parsing.report_model import (
    Section,
    Field,
    Group,
    SectionType,
    FontSpec,
    FormatSpec,
)
from ..utils.logger import get_logger
from .font_mapper import FontMapper


class CoordinateConverter:
    """Converts coordinates between different measurement units.

    Crystal Reports uses twips (1/1440 inch).
    Oracle Reports typically uses points (1/72 inch).

    Conversion formulas:
    - 1 inch = 1440 twips = 72 points = 2.54 cm
    - points = twips / 20
    - inches = twips / 1440
    - cm = (twips / 1440) * 2.54
    """

    # Conversion constants
    TWIPS_PER_INCH = 1440.0
    POINTS_PER_INCH = 72.0
    CM_PER_INCH = 2.54
    TWIPS_PER_POINT = TWIPS_PER_INCH / POINTS_PER_INCH  # 20.0

    @staticmethod
    def twips_to_points(twips: float) -> float:
        """Convert twips to points.

        Args:
            twips: Value in twips (1/1440 inch)

        Returns:
            Value in points (1/72 inch)
        """
        return twips / CoordinateConverter.TWIPS_PER_POINT

    @staticmethod
    def twips_to_inches(twips: float) -> float:
        """Convert twips to inches.

        Args:
            twips: Value in twips (1/1440 inch)

        Returns:
            Value in inches
        """
        return twips / CoordinateConverter.TWIPS_PER_INCH

    @staticmethod
    def twips_to_cm(twips: float) -> float:
        """Convert twips to centimeters.

        Args:
            twips: Value in twips (1/1440 inch)

        Returns:
            Value in centimeters
        """
        inches = twips / CoordinateConverter.TWIPS_PER_INCH
        return inches * CoordinateConverter.CM_PER_INCH

    @staticmethod
    def points_to_twips(points: float) -> int:
        """Convert points to twips.

        Args:
            points: Value in points (1/72 inch)

        Returns:
            Value in twips (1/1440 inch)
        """
        return int(points * CoordinateConverter.TWIPS_PER_POINT)

    @staticmethod
    def inches_to_twips(inches: float) -> int:
        """Convert inches to twips.

        Args:
            inches: Value in inches

        Returns:
            Value in twips (1/1440 inch)
        """
        return int(inches * CoordinateConverter.TWIPS_PER_INCH)

    @staticmethod
    def cm_to_twips(cm: float) -> int:
        """Convert centimeters to twips.

        Args:
            cm: Value in centimeters

        Returns:
            Value in twips (1/1440 inch)
        """
        inches = cm / CoordinateConverter.CM_PER_INCH
        return int(inches * CoordinateConverter.TWIPS_PER_INCH)

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Convert a value from one unit to another.

        Args:
            value: Value to convert
            from_unit: Source unit ('twips', 'points', 'inches', 'cm')
            to_unit: Target unit ('twips', 'points', 'inches', 'cm')

        Returns:
            Converted value
        """
        # Normalize to lowercase
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        # If same unit, no conversion needed
        if from_unit == to_unit:
            return value

        # First convert to inches as intermediate
        if from_unit == "twips":
            inches = cls.twips_to_inches(value)
        elif from_unit == "points":
            inches = value / cls.POINTS_PER_INCH
        elif from_unit == "inches":
            inches = value
        elif from_unit == "cm":
            inches = value / cls.CM_PER_INCH
        else:
            raise ValueError(f"Unknown source unit: {from_unit}")

        # Then convert from inches to target unit
        if to_unit == "twips":
            return cls.inches_to_twips(inches)
        elif to_unit == "points":
            return inches * cls.POINTS_PER_INCH
        elif to_unit == "inches":
            return inches
        elif to_unit == "cm":
            return inches * cls.CM_PER_INCH
        else:
            raise ValueError(f"Unknown target unit: {to_unit}")


@dataclass
class OracleFrame:
    """Oracle Reports frame definition."""

    name: str
    frame_type: str = "margin"  # margin, header, body, trailer, repeating
    source_group: Optional[str] = None  # For repeating frames
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    vertical_elasticity: str = "expand"  # fixed, expand, contract, variable
    horizontal_elasticity: str = "fixed"
    print_direction: str = "down"  # down, across
    min_width_widget: Optional[str] = None
    children: list["OracleFrame"] = field(default_factory=list)
    fields: list["OracleField"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "frame_type": self.frame_type,
            "source_group": self.source_group,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "vertical_elasticity": self.vertical_elasticity,
            "horizontal_elasticity": self.horizontal_elasticity,
            "print_direction": self.print_direction,
            "children": [c.to_dict() for c in self.children],
            "fields": [f.to_dict() for f in self.fields],
        }


@dataclass
class OracleField:
    """Oracle Reports field definition."""

    name: str
    source: str  # Column name or formula reference
    source_type: str = "column"  # column, formula, parameter, file, text
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 14.0
    font_name: str = "Arial"
    font_size: int = 10
    font_style: str = "plain"  # plain, bold, italic, bolditalic
    format_mask: Optional[str] = None
    horizontal_alignment: str = "start"  # start, center, end, flush
    vertical_alignment: str = "top"  # top, center, bottom
    foreground_color: str = "black"
    background_color: str = "white"
    visible: bool = True
    format_trigger: Optional[str] = None

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
            "font_name": self.font_name,
            "font_size": self.font_size,
            "font_style": self.font_style,
            "format_mask": self.format_mask,
            "horizontal_alignment": self.horizontal_alignment,
            "vertical_alignment": self.vertical_alignment,
            "foreground_color": self.foreground_color,
            "background_color": self.background_color,
            "visible": self.visible,
            "format_trigger": self.format_trigger,
        }


@dataclass
class OracleLayout:
    """Complete Oracle Reports layout definition."""

    page_width: float = 612.0  # 8.5 inches in points
    page_height: float = 792.0  # 11 inches in points
    orientation: str = "portrait"
    left_margin: float = 36.0
    right_margin: float = 36.0
    top_margin: float = 36.0
    bottom_margin: float = 36.0

    # Main layout frames
    margin_frame: Optional[OracleFrame] = None
    header_frame: Optional[OracleFrame] = None
    body_frame: Optional[OracleFrame] = None
    trailer_frame: Optional[OracleFrame] = None

    # All frames (flat list for reference)
    all_frames: list[OracleFrame] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "page_width": self.page_width,
            "page_height": self.page_height,
            "orientation": self.orientation,
            "margins": {
                "left": self.left_margin,
                "right": self.right_margin,
                "top": self.top_margin,
                "bottom": self.bottom_margin,
            },
            "margin_frame": self.margin_frame.to_dict() if self.margin_frame else None,
            "header_frame": self.header_frame.to_dict() if self.header_frame else None,
            "body_frame": self.body_frame.to_dict() if self.body_frame else None,
            "trailer_frame": self.trailer_frame.to_dict() if self.trailer_frame else None,
        }


class LayoutMapper:
    """Maps Crystal Reports layout to Oracle Reports layout model."""

    # Crystal section type to Oracle frame type mapping
    SECTION_FRAME_MAP = {
        SectionType.REPORT_HEADER: ("M_REPORT_HEADER", "margin"),
        SectionType.PAGE_HEADER: ("M_PAGE_HEADER", "header"),
        SectionType.GROUP_HEADER: ("R_G_{group}", "repeating"),
        SectionType.DETAIL: ("R_G_DETAIL", "repeating"),
        SectionType.GROUP_FOOTER: ("M_G_{group}_FTR", "margin"),
        SectionType.PAGE_FOOTER: ("M_PAGE_FOOTER", "trailer"),
        SectionType.REPORT_FOOTER: ("M_REPORT_FOOTER", "margin"),
    }

    # Alignment mapping
    HALIGN_MAP = {
        "left": "start",
        "center": "center",
        "right": "end",
        "justify": "flush",
    }

    VALIGN_MAP = {
        "top": "top",
        "middle": "center",
        "bottom": "bottom",
    }

    def __init__(
        self,
        field_prefix: str = "F_",
        coordinate_unit: str = "points",
        default_font: str = "Arial",
        default_font_size: int = 10,
        font_config_path: Optional[str] = None,
    ):
        """Initialize the layout mapper.

        Args:
            field_prefix: Prefix for Oracle field names.
            coordinate_unit: Unit for coordinates ('points', 'inches', 'cm').
            default_font: Default font name.
            default_font_size: Default font size.
            font_config_path: Optional path to font_mappings.yaml configuration.
        """
        self.field_prefix = field_prefix
        self.coordinate_unit = coordinate_unit
        self.default_font = default_font
        self.default_font_size = default_font_size
        self.logger = get_logger("layout_mapper")
        self.converter = CoordinateConverter()

        # Initialize font mapper
        self.font_mapper = FontMapper(
            config_path=font_config_path,
            default_font=default_font,
            default_size=default_font_size,
        )

        # Frame counter for unique names
        self._frame_counter = 0
        self._field_counter = 0

        # Storage for format triggers
        self._format_triggers = []

    def map_layout(
        self,
        sections: list[Section],
        groups: list[Group],
        page_width: float = 612.0,
        page_height: float = 792.0,
        condition_mapper: Optional[Any] = None,
    ) -> OracleLayout:
        """Map Crystal sections to Oracle layout.

        Args:
            sections: List of Crystal report sections.
            groups: List of report groups.
            page_width: Page width in points.
            page_height: Page height in points.
            condition_mapper: Optional ConditionMapper for converting suppress conditions.

        Returns:
            OracleLayout with mapped frames and fields.
        """
        self.logger.info(f"Mapping layout: {len(sections)} sections, {len(groups)} groups")

        # Reset counters and triggers
        self._frame_counter = 0
        self._field_counter = 0
        self._format_triggers = []
        self._condition_mapper = condition_mapper

        layout = OracleLayout(
            page_width=page_width,
            page_height=page_height,
        )

        # Calculate content area
        content_width = page_width - layout.left_margin - layout.right_margin
        current_y = layout.top_margin

        # Process sections by type
        report_headers = [s for s in sections if s.section_type == SectionType.REPORT_HEADER]
        page_headers = [s for s in sections if s.section_type == SectionType.PAGE_HEADER]
        group_headers = [s for s in sections if s.section_type == SectionType.GROUP_HEADER]
        details = [s for s in sections if s.section_type == SectionType.DETAIL]
        group_footers = [s for s in sections if s.section_type == SectionType.GROUP_FOOTER]
        page_footers = [s for s in sections if s.section_type == SectionType.PAGE_FOOTER]
        report_footers = [s for s in sections if s.section_type == SectionType.REPORT_FOOTER]

        # Create main margin frame
        layout.margin_frame = OracleFrame(
            name="M_MAIN",
            frame_type="margin",
            x=layout.left_margin,
            y=layout.top_margin,
            width=content_width,
            height=page_height - layout.top_margin - layout.bottom_margin,
        )
        layout.all_frames.append(layout.margin_frame)

        # Map report header
        for section in report_headers:
            frame = self._map_section(section, content_width, groups)
            frame.y = current_y
            current_y += frame.height
            layout.margin_frame.children.append(frame)
            layout.all_frames.append(frame)

        # Create header frame for page headers
        if page_headers:
            layout.header_frame = OracleFrame(
                name="M_PAGE_HEADER",
                frame_type="header",
                x=0,
                y=current_y,
                width=content_width,
                height=sum(s.height for s in page_headers),
            )
            layout.all_frames.append(layout.header_frame)

            for section in page_headers:
                frame = self._map_section(section, content_width, groups)
                layout.header_frame.children.append(frame)
                layout.all_frames.append(frame)

            current_y += layout.header_frame.height

        # Create body frame with repeating frames
        body_height = sum(s.height for s in group_headers + details + group_footers)
        layout.body_frame = OracleFrame(
            name="M_BODY",
            frame_type="body",
            x=0,
            y=current_y,
            width=content_width,
            height=body_height,
            vertical_elasticity="expand",
        )
        layout.all_frames.append(layout.body_frame)

        # Map group headers and detail as nested repeating frames
        self._map_body_sections(
            layout.body_frame,
            group_headers,
            details,
            group_footers,
            groups,
            content_width,
        )

        current_y += body_height

        # Create trailer frame for page footers
        if page_footers:
            layout.trailer_frame = OracleFrame(
                name="M_PAGE_FOOTER",
                frame_type="trailer",
                x=0,
                y=page_height - layout.bottom_margin - sum(s.height for s in page_footers),
                width=content_width,
                height=sum(s.height for s in page_footers),
            )
            layout.all_frames.append(layout.trailer_frame)

            for section in page_footers:
                frame = self._map_section(section, content_width, groups)
                layout.trailer_frame.children.append(frame)
                layout.all_frames.append(frame)

        # Map report footers
        for section in report_footers:
            frame = self._map_section(section, content_width, groups)
            frame.y = current_y
            current_y += frame.height
            layout.margin_frame.children.append(frame)
            layout.all_frames.append(frame)

        self.logger.info(f"Created {len(layout.all_frames)} frames")
        return layout

    def _map_body_sections(
        self,
        body_frame: OracleFrame,
        group_headers: list[Section],
        details: list[Section],
        group_footers: list[Section],
        groups: list[Group],
        width: float,
    ) -> None:
        """Map body sections with proper nesting for groups."""
        current_y = 0

        # Sort sections by group number for proper nesting
        group_headers_by_num = {}
        group_footers_by_num = {}

        for section in group_headers:
            num = section.group_number or 0
            group_headers_by_num[num] = section

        for section in group_footers:
            num = section.group_number or 0
            group_footers_by_num[num] = section

        # Create nested repeating frames for groups
        def create_group_frames(
            parent: OracleFrame,
            group_index: int,
            y_offset: float,
        ) -> float:
            if group_index >= len(groups):
                # Base case: add detail section
                for section in details:
                    detail_frame = self._map_section(section, width, groups)
                    detail_frame.name = "R_G_DETAIL"
                    detail_frame.frame_type = "repeating"
                    detail_frame.source_group = "G_DETAIL"
                    detail_frame.y = y_offset
                    parent.children.append(detail_frame)
                    y_offset += detail_frame.height
                return y_offset

            group = groups[group_index]
            group_num = group_index + 1

            # Create repeating frame for this group
            group_frame = OracleFrame(
                name=f"R_G_{group.name}",
                frame_type="repeating",
                source_group=group.name,
                x=0,
                y=y_offset,
                width=width,
                vertical_elasticity="expand",
            )

            inner_y = 0

            # Add group header if exists
            header = group_headers_by_num.get(group_num)
            if header:
                header_frame = self._map_section(header, width, groups)
                header_frame.y = inner_y
                group_frame.children.append(header_frame)
                inner_y += header_frame.height

            # Recurse for nested groups/detail
            inner_y = create_group_frames(group_frame, group_index + 1, inner_y)

            # Add group footer if exists
            footer = group_footers_by_num.get(group_num)
            if footer:
                footer_frame = self._map_section(footer, width, groups)
                footer_frame.y = inner_y
                group_frame.children.append(footer_frame)
                inner_y += footer_frame.height

            group_frame.height = inner_y
            parent.children.append(group_frame)

            return y_offset + inner_y

        # Start building from outermost group
        if groups:
            create_group_frames(body_frame, 0, current_y)
        else:
            # No groups - just detail section
            for section in details:
                detail_frame = self._map_section(section, width, groups)
                detail_frame.name = "R_G_DETAIL"
                detail_frame.frame_type = "repeating"
                detail_frame.y = current_y
                body_frame.children.append(detail_frame)
                current_y += detail_frame.height

    def _map_section(
        self,
        section: Section,
        width: float,
        groups: list[Group],
    ) -> OracleFrame:
        """Map a single Crystal section to an Oracle frame."""
        self._frame_counter += 1

        # Determine frame name and type
        frame_name, frame_type = self.SECTION_FRAME_MAP.get(
            section.section_type,
            (f"M_SECTION_{self._frame_counter}", "margin"),
        )

        # Handle group-specific naming
        if "{group}" in frame_name:
            group_num = section.group_number or 1
            if group_num <= len(groups):
                group_name = groups[group_num - 1].name
            else:
                group_name = f"G{group_num}"
            frame_name = frame_name.replace("{group}", group_name)

        # Convert section height from twips to target unit
        converted_height = self.converter.convert(
            section.height, "twips", self.coordinate_unit
        )

        frame = OracleFrame(
            name=frame_name,
            frame_type=frame_type,
            x=0,
            y=0,
            width=width,
            height=converted_height,
            source_group=frame_name.replace("R_", "") if frame_type == "repeating" else None,
        )

        # Map fields in section
        for crystal_field in section.fields:
            oracle_field = self._map_field(crystal_field)
            frame.fields.append(oracle_field)

        return frame

    def _map_field(self, crystal_field: Field) -> OracleField:
        """Map a Crystal field to an Oracle field."""
        self._field_counter += 1

        # Create Oracle field name
        name = crystal_field.name
        if not name.upper().startswith(self.field_prefix.upper()):
            name = f"{self.field_prefix}{name}"
        name = name.upper().replace(" ", "_")

        # Determine source
        source = crystal_field.source
        source_type = "column"

        if crystal_field.source_type == "formula":
            source = source.lstrip("@")
            source_type = "formula"
        elif crystal_field.source_type == "parameter":
            source = source.lstrip("?")
            source_type = "parameter"
        elif crystal_field.source_type == "special":
            source_type = "file"  # Oracle uses file for special fields
        else:
            # Database field - extract column name
            if "." in source:
                source = source.split(".")[-1]
            source = source.upper().replace(" ", "_")

        # Map font using FontMapper
        font_info = self.font_mapper.get_font_info(
            crystal_font=crystal_field.font.name,
            crystal_size=crystal_field.font.size,
            bold=crystal_field.font.bold,
            italic=crystal_field.font.italic,
            underline=crystal_field.font.underline,
        )

        # Map alignment
        h_align = self.HALIGN_MAP.get(
            crystal_field.format.horizontal_alignment,
            "start",
        )
        v_align = self.VALIGN_MAP.get(
            crystal_field.format.vertical_alignment,
            "top",
        )

        # Convert coordinates from twips to target unit
        converted_x = self.converter.convert(crystal_field.x, "twips", self.coordinate_unit)
        converted_y = self.converter.convert(crystal_field.y, "twips", self.coordinate_unit)
        converted_width = self.converter.convert(crystal_field.width, "twips", self.coordinate_unit)
        converted_height = self.converter.convert(crystal_field.height, "twips", self.coordinate_unit)

        # Handle suppress conditions and generate format triggers
        format_trigger_name = None

        if hasattr(self, '_condition_mapper') and self._condition_mapper:
            # Check for explicit suppress condition
            if crystal_field.suppress_condition:
                trigger = self._condition_mapper.convert_suppress_condition(
                    crystal_field.suppress_condition,
                    field_name=name,
                )
                self._format_triggers.append(trigger)
                format_trigger_name = trigger.name
            # Check for suppress_if_zero or suppress_if_blank
            elif crystal_field.format.suppress_if_zero or crystal_field.format.suppress_if_blank:
                trigger = self._condition_mapper.convert_suppress_if_conditions(
                    crystal_field.format,
                    field_name=source,  # Use the actual field name for reference
                )
                if trigger:
                    self._format_triggers.append(trigger)
                    format_trigger_name = trigger.name

        return OracleField(
            name=name,
            source=source,
            source_type=source_type,
            x=converted_x,
            y=converted_y,
            width=converted_width,
            height=converted_height,
            font_name=font_info["oracle_font"],
            font_size=font_info["oracle_size"],
            font_style=font_info["oracle_style"],
            format_mask=crystal_field.format.format_string,
            horizontal_alignment=h_align,
            vertical_alignment=v_align,
            foreground_color=crystal_field.font.color or "black",
            background_color=crystal_field.background_color or "white",
            visible=crystal_field.suppress_condition is None,
            format_trigger=format_trigger_name,
        )

    def get_format_triggers(self) -> list:
        """Get all format triggers generated during layout mapping.

        Returns:
            List of FormatTrigger objects.
        """
        return self._format_triggers if hasattr(self, '_format_triggers') else []

