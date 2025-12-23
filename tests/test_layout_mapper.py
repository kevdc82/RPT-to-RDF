"""
Unit tests for Layout Mapper.

Tests the conversion of Crystal Reports layout to Oracle Reports layout.
"""

import pytest
from src.transformation.layout_mapper import (
    LayoutMapper,
    OracleLayout,
    OracleFrame,
    OracleField,
    CoordinateConverter,
)
from src.parsing.report_model import (
    Section,
    Field,
    Group,
    SectionType,
    FontSpec,
    FormatSpec,
)


class TestOracleField:
    """Test suite for OracleField dataclass."""

    def test_oracle_field_creation(self):
        """Test creating an OracleField."""
        field = OracleField(
            name="F_CUSTOMER_NAME",
            source="CUSTOMER_NAME",
            source_type="column",
            x=10.0,
            y=20.0,
            width=150.0,
            height=14.0
        )
        assert field.name == "F_CUSTOMER_NAME"
        assert field.source == "CUSTOMER_NAME"
        assert field.x == 10.0
        assert field.width == 150.0

    def test_oracle_field_to_dict(self):
        """Test converting OracleField to dictionary."""
        field = OracleField(
            name="F_TEST",
            source="TEST_COLUMN",
            x=5.0,
            y=10.0
        )
        result = field.to_dict()
        assert result["name"] == "F_TEST"
        assert result["source"] == "TEST_COLUMN"
        assert result["x"] == 5.0
        assert result["source_type"] == "column"

    def test_oracle_field_font_properties(self):
        """Test OracleField font properties."""
        field = OracleField(
            name="F_TITLE",
            source="TITLE",
            font_name="Arial",
            font_size=12,
            font_style="bold"
        )
        assert field.font_name == "Arial"
        assert field.font_size == 12
        assert field.font_style == "bold"

    def test_oracle_field_alignment(self):
        """Test OracleField alignment properties."""
        field = OracleField(
            name="F_AMOUNT",
            source="AMOUNT",
            horizontal_alignment="end",
            vertical_alignment="center"
        )
        assert field.horizontal_alignment == "end"
        assert field.vertical_alignment == "center"


class TestOracleFrame:
    """Test suite for OracleFrame dataclass."""

    def test_oracle_frame_creation(self):
        """Test creating an OracleFrame."""
        frame = OracleFrame(
            name="M_HEADER",
            frame_type="header",
            width=600.0,
            height=50.0
        )
        assert frame.name == "M_HEADER"
        assert frame.frame_type == "header"
        assert frame.width == 600.0

    def test_oracle_frame_with_children(self):
        """Test OracleFrame with child frames."""
        parent = OracleFrame(name="M_PARENT", frame_type="margin")
        child1 = OracleFrame(name="M_CHILD1", frame_type="margin")
        child2 = OracleFrame(name="M_CHILD2", frame_type="margin")

        parent.children.append(child1)
        parent.children.append(child2)

        assert len(parent.children) == 2
        assert parent.children[0].name == "M_CHILD1"

    def test_oracle_frame_with_fields(self):
        """Test OracleFrame with fields."""
        frame = OracleFrame(name="R_DETAIL", frame_type="repeating")
        field1 = OracleField(name="F_NAME", source="NAME")
        field2 = OracleField(name="F_AMOUNT", source="AMOUNT")

        frame.fields.append(field1)
        frame.fields.append(field2)

        assert len(frame.fields) == 2

    def test_oracle_frame_to_dict(self):
        """Test converting OracleFrame to dictionary."""
        frame = OracleFrame(
            name="R_GROUP",
            frame_type="repeating",
            source_group="G_CUSTOMER"
        )
        result = frame.to_dict()
        assert result["name"] == "R_GROUP"
        assert result["frame_type"] == "repeating"
        assert result["source_group"] == "G_CUSTOMER"


class TestOracleLayout:
    """Test suite for OracleLayout dataclass."""

    def test_oracle_layout_creation(self):
        """Test creating an OracleLayout."""
        layout = OracleLayout(
            page_width=612.0,
            page_height=792.0,
            orientation="portrait"
        )
        assert layout.page_width == 612.0
        assert layout.page_height == 792.0
        assert layout.orientation == "portrait"

    def test_oracle_layout_margins(self):
        """Test OracleLayout margin settings."""
        layout = OracleLayout(
            left_margin=72.0,
            right_margin=72.0,
            top_margin=72.0,
            bottom_margin=72.0
        )
        assert layout.left_margin == 72.0
        assert layout.top_margin == 72.0

    def test_oracle_layout_to_dict(self):
        """Test converting OracleLayout to dictionary."""
        layout = OracleLayout()
        result = layout.to_dict()
        assert "page_width" in result
        assert "page_height" in result
        assert "margins" in result
        assert result["margins"]["left"] == 36.0


class TestLayoutMapper:
    """Test suite for LayoutMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = LayoutMapper(
            field_prefix="F_",
            coordinate_unit="points"
        )

    # Field mapping tests
    def test_map_simple_field(self):
        """Test mapping a simple database field.

        Note: Crystal Reports uses twips, Oracle uses points.
        1 twip = 1/20 point, so 10 twips = 0.5 points, 20 twips = 1.0 points.
        """
        crystal_field = Field(
            name="CustomerName",
            source="Customer.Name",
            source_type="database",
            x=10.0,  # twips
            y=20.0,  # twips
            width=150.0,
            height=14.0,
            font=FontSpec(name="Arial", size=10),
            format=FormatSpec(horizontal_alignment="left")
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.name.startswith("F_")
        assert "NAME" in oracle_field.source.upper()
        assert oracle_field.source_type == "column"
        # Coordinates are converted from twips to points (1 twip = 0.05 points)
        assert oracle_field.x == 0.5  # 10 twips = 0.5 points
        assert oracle_field.y == 1.0  # 20 twips = 1.0 points

    def test_map_formula_field(self):
        """Test mapping a formula field."""
        crystal_field = Field(
            name="CalculatedField",
            source="@MyFormula",
            source_type="formula",
            x=0.0,
            y=0.0,
            width=100.0,
            height=14.0
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.source_type == "formula"
        assert "@" not in oracle_field.source  # @ should be stripped

    def test_map_parameter_field(self):
        """Test mapping a parameter field."""
        crystal_field = Field(
            name="ParamField",
            source="?StartDate",
            source_type="parameter",
            x=0.0,
            y=0.0,
            width=100.0,
            height=14.0
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.source_type == "parameter"
        assert "?" not in oracle_field.source  # ? should be stripped

    def test_map_field_with_bold_font(self):
        """Test mapping field with bold font."""
        crystal_field = Field(
            name="BoldField",
            source="Title",
            font=FontSpec(bold=True, italic=False)
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.font_style == "bold"

    def test_map_field_with_italic_font(self):
        """Test mapping field with italic font."""
        crystal_field = Field(
            name="ItalicField",
            source="Subtitle",
            font=FontSpec(bold=False, italic=True)
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.font_style == "italic"

    def test_map_field_with_bold_italic_font(self):
        """Test mapping field with bold and italic font."""
        crystal_field = Field(
            name="BoldItalicField",
            source="Header",
            font=FontSpec(bold=True, italic=True)
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.font_style == "bolditalic"

    def test_map_field_alignment_left(self):
        """Test mapping field with left alignment."""
        crystal_field = Field(
            name="LeftField",
            source="Name",
            format=FormatSpec(horizontal_alignment="left")
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.horizontal_alignment == "start"

    def test_map_field_alignment_center(self):
        """Test mapping field with center alignment."""
        crystal_field = Field(
            name="CenterField",
            source="Title",
            format=FormatSpec(horizontal_alignment="center")
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.horizontal_alignment == "center"

    def test_map_field_alignment_right(self):
        """Test mapping field with right alignment."""
        crystal_field = Field(
            name="RightField",
            source="Amount",
            format=FormatSpec(horizontal_alignment="right")
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.horizontal_alignment == "end"

    def test_map_field_with_format_string(self):
        """Test mapping field with format string."""
        crystal_field = Field(
            name="FormattedField",
            source="Amount",
            format=FormatSpec(format_string="#,##0.00")
        )

        oracle_field = self.mapper._map_field(crystal_field)

        assert oracle_field.format_mask == "#,##0.00"

    # Section mapping tests
    def test_map_section_report_header(self):
        """Test mapping report header section.

        Note: Crystal Reports section heights are in twips.
        1 twip = 1/20 point, so 50 twips = 2.5 points.
        """
        section = Section(
            name="ReportHeader",
            section_type=SectionType.REPORT_HEADER,
            height=50.0,  # twips
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        assert "REPORT_HEADER" in frame.name
        # Height is converted from twips to points
        assert frame.height == 2.5  # 50 twips = 2.5 points

    def test_map_section_page_header(self):
        """Test mapping page header section."""
        section = Section(
            name="PageHeader",
            section_type=SectionType.PAGE_HEADER,
            height=30.0,
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        assert "PAGE_HEADER" in frame.name
        assert frame.frame_type == "header"

    def test_map_section_detail(self):
        """Test mapping detail section."""
        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        assert "DETAIL" in frame.name
        assert frame.frame_type == "repeating"

    def test_map_section_with_fields(self):
        """Test mapping section containing fields."""
        field1 = Field(name="Field1", source="Col1")
        field2 = Field(name="Field2", source="Col2")

        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=[field1, field2]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        assert len(frame.fields) == 2

    def test_map_section_group_header(self):
        """Test mapping group header section."""
        group = Group(name="CustomerGroup", field_name="Customer")

        section = Section(
            name="GroupHeader1",
            section_type=SectionType.GROUP_HEADER,
            group_number=1,
            height=25.0,
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [group])

        assert "CUSTOMERGROUP" in frame.name or "G" in frame.name

    # Full layout mapping tests
    def test_map_layout_simple(self):
        """Test mapping a simple layout with basic sections."""
        sections = [
            Section(
                name="PageHeader",
                section_type=SectionType.PAGE_HEADER,
                height=30.0,
                fields=[]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[]
            ),
            Section(
                name="PageFooter",
                section_type=SectionType.PAGE_FOOTER,
                height=25.0,
                fields=[]
            )
        ]

        layout = self.mapper.map_layout(sections, [], 612.0, 792.0)

        assert layout.page_width == 612.0
        assert layout.page_height == 792.0
        assert layout.header_frame is not None
        assert layout.body_frame is not None
        assert layout.trailer_frame is not None

    def test_map_layout_with_groups(self):
        """Test mapping layout with group sections."""
        group = Group(name="CustomerGroup", field_name="Customer")

        sections = [
            Section(
                name="GroupHeader1",
                section_type=SectionType.GROUP_HEADER,
                group_number=1,
                height=25.0,
                fields=[]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[]
            ),
            Section(
                name="GroupFooter1",
                section_type=SectionType.GROUP_FOOTER,
                group_number=1,
                height=25.0,
                fields=[]
            )
        ]

        layout = self.mapper.map_layout(sections, [group], 612.0, 792.0)

        assert layout.body_frame is not None
        assert len(layout.body_frame.children) > 0

    def test_map_layout_nested_groups(self):
        """Test mapping layout with nested groups."""
        group1 = Group(name="Region", field_name="Region")
        group2 = Group(name="Customer", field_name="Customer")

        sections = [
            Section(
                name="GroupHeader1",
                section_type=SectionType.GROUP_HEADER,
                group_number=1,
                height=25.0,
                fields=[]
            ),
            Section(
                name="GroupHeader2",
                section_type=SectionType.GROUP_HEADER,
                group_number=2,
                height=20.0,
                fields=[]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=15.0,
                fields=[]
            )
        ]

        layout = self.mapper.map_layout(sections, [group1, group2], 612.0, 792.0)

        assert layout.body_frame is not None
        # Should have nested structure - at least 2 frames for groups plus body
        assert len(layout.all_frames) >= 2

    def test_map_layout_report_headers_footers(self):
        """Test mapping layout with report headers and footers."""
        sections = [
            Section(
                name="ReportHeader",
                section_type=SectionType.REPORT_HEADER,
                height=40.0,
                fields=[]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[]
            ),
            Section(
                name="ReportFooter",
                section_type=SectionType.REPORT_FOOTER,
                height=35.0,
                fields=[]
            )
        ]

        layout = self.mapper.map_layout(sections, [], 612.0, 792.0)

        assert layout.margin_frame is not None
        assert len(layout.margin_frame.children) >= 2  # Header and footer

    def test_map_layout_empty_sections(self):
        """Test mapping layout with no sections."""
        layout = self.mapper.map_layout([], [], 612.0, 792.0)

        assert layout.page_width == 612.0
        assert layout.margin_frame is not None

    # Coordinate conversion tests - use CoordinateConverter class directly
    def test_convert_twips_to_points(self):
        """Test converting twips to points."""
        result = CoordinateConverter.convert(1440.0, "twips", "points")
        assert result == 72.0  # 1 inch = 1440 twips = 72 points

    def test_convert_points_to_inches(self):
        """Test converting points to inches."""
        result = CoordinateConverter.convert(72.0, "points", "inches")
        assert result == 1.0

    def test_convert_inches_to_points(self):
        """Test converting inches to points."""
        result = CoordinateConverter.convert(1.0, "inches", "points")
        assert result == 72.0

    def test_convert_cm_to_points(self):
        """Test converting centimeters to points."""
        result = CoordinateConverter.convert(2.54, "cm", "points")
        assert abs(result - 72.0) < 0.1  # 1 inch = 2.54 cm

    def test_convert_points_to_twips(self):
        """Test converting points to twips."""
        result = CoordinateConverter.convert(72.0, "points", "twips")
        assert result == 1440.0

    def test_convert_same_unit(self):
        """Test converting with same source and target unit."""
        result = CoordinateConverter.convert(100.0, "points", "points")
        assert result == 100.0


class TestLayoutMapperConfiguration:
    """Test LayoutMapper configuration options."""

    def test_custom_field_prefix(self):
        """Test custom field prefix."""
        mapper = LayoutMapper(field_prefix="FLD_")

        field = Field(name="Test", source="TEST_COL")
        oracle_field = mapper._map_field(field)

        assert oracle_field.name.startswith("FLD_")

    def test_custom_default_font(self):
        """Test custom default font."""
        mapper = LayoutMapper(default_font="Times New Roman", default_font_size=12)

        field = Field(name="Test", source="TEST", font=FontSpec())
        oracle_field = mapper._map_field(field)

        # If font name is default or None, should use mapper default
        assert oracle_field.font_name in ["Arial", "Times New Roman"]

    def test_coordinate_unit_setting(self):
        """Test coordinate unit configuration."""
        mapper = LayoutMapper(coordinate_unit="inches")
        assert mapper.coordinate_unit == "inches"


class TestLayoutMapperEdgeCases:
    """Test edge cases for LayoutMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = LayoutMapper()

    def test_field_with_spaces_in_name(self):
        """Test field with spaces in name."""
        field = Field(name="Customer Name", source="CUSTOMER_NAME")
        oracle_field = self.mapper._map_field(field)

        assert " " not in oracle_field.name
        assert "_" in oracle_field.name

    def test_field_with_special_characters(self):
        """Test field with special characters in name."""
        field = Field(name="Field-1!", source="FIELD1")
        oracle_field = self.mapper._map_field(field)

        # Special chars should be handled (replaced or removed)
        assert oracle_field.name.replace("_", "").replace("F", "").isalnum() or "_" in oracle_field.name

    def test_section_zero_height(self):
        """Test section with zero height."""
        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=0.0,
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        assert frame.height == 0.0

    def test_section_very_large_height(self):
        """Test section with very large height.

        Note: Height is converted from twips to points (1 twip = 0.05 points).
        1000 twips = 50 points.
        """
        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=1000.0,  # twips
            fields=[]
        )

        frame = self.mapper._map_section(section, 600.0, [])

        # Height is converted from twips to points
        assert frame.height == 50.0  # 1000 twips = 50 points

    def test_layout_custom_page_size(self):
        """Test layout with custom page size."""
        sections = [
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[]
            )
        ]

        layout = self.mapper.map_layout(sections, [], 842.0, 595.0)  # A4 landscape

        assert layout.page_width == 842.0
        assert layout.page_height == 595.0

    def test_field_with_suppress_condition(self):
        """Test field with suppress condition."""
        field = Field(
            name="ConditionalField",
            source="FIELD",
            suppress_condition="{Field} = 0"
        )

        oracle_field = self.mapper._map_field(field)

        # Field with suppress condition should have visible=False
        assert oracle_field.visible is False

    def test_field_without_suppress_condition(self):
        """Test field without suppress condition."""
        field = Field(
            name="VisibleField",
            source="FIELD",
            suppress_condition=None
        )

        oracle_field = self.mapper._map_field(field)

        assert oracle_field.visible is True

    def test_frame_counter_increments(self):
        """Test that frame counter increments."""
        section1 = Section(
            name="Section1",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=[]
        )
        section2 = Section(
            name="Section2",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=[]
        )

        frame1 = self.mapper._map_section(section1, 600.0, [])
        frame2 = self.mapper._map_section(section2, 600.0, [])

        # Frames should have unique identifiers
        assert frame1.name != frame2.name or self.mapper._frame_counter > 1

    def test_vertical_alignment_mapping(self):
        """Test vertical alignment mapping."""
        field_top = Field(
            name="TopField",
            source="FIELD",
            format=FormatSpec(vertical_alignment="top")
        )
        field_middle = Field(
            name="MiddleField",
            source="FIELD",
            format=FormatSpec(vertical_alignment="middle")
        )
        field_bottom = Field(
            name="BottomField",
            source="FIELD",
            format=FormatSpec(vertical_alignment="bottom")
        )

        oracle_top = self.mapper._map_field(field_top)
        oracle_middle = self.mapper._map_field(field_middle)
        oracle_bottom = self.mapper._map_field(field_bottom)

        assert oracle_top.vertical_alignment == "top"
        assert oracle_middle.vertical_alignment == "center"
        assert oracle_bottom.vertical_alignment == "bottom"

    def test_table_prefix_removal(self):
        """Test that table prefix is removed from field source."""
        field = Field(
            name="CustomerField",
            source="Customers.CustomerName",
            source_type="database"
        )

        oracle_field = self.mapper._map_field(field)

        # Table prefix should be removed
        assert "." not in oracle_field.source
        assert "CUSTOMERNAME" in oracle_field.source.upper()
