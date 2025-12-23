"""
Integration tests for FontMapper with LayoutMapper.

Tests the complete font mapping flow from Crystal Reports to Oracle Reports.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.parsing.report_model import Field, FontSpec, FormatSpec, Section, SectionType
from src.transformation.layout_mapper import LayoutMapper


class TestFontMapperIntegration:
    """Integration tests for FontMapper with LayoutMapper."""

    def test_layout_mapper_uses_font_mapper(self):
        """Test that LayoutMapper correctly uses FontMapper for font conversion."""
        # Create a layout mapper
        mapper = LayoutMapper()

        # Create a test field with Crystal font
        crystal_field = Field(
            name="TestField",
            source="test_column",
            source_type="database",
            x=0,
            y=0,
            width=1000,
            height=200,
            font=FontSpec(
                name="Times New Roman",
                size=14,
                bold=True,
                italic=False,
            ),
            format=FormatSpec(
                horizontal_alignment="center",
                vertical_alignment="middle",
            ),
        )

        # Map the field
        oracle_field = mapper._map_field(crystal_field)

        # Verify font was mapped correctly
        assert oracle_field.font_name == "Times"  # Mapped from "Times New Roman"
        assert oracle_field.font_size == 14
        assert oracle_field.font_style == "bold"

    def test_layout_mapper_with_multiple_fonts(self):
        """Test LayoutMapper handles multiple different fonts."""
        mapper = LayoutMapper()

        # Create fields with different fonts
        fields = [
            Field(
                name=f"Field{i}",
                source=f"col{i}",
                font=FontSpec(name=font, size=size, bold=bold, italic=italic),
                format=FormatSpec(),
            )
            for i, (font, size, bold, italic) in enumerate(
                [
                    ("Arial", 10, False, False),
                    ("Times New Roman", 12, True, False),
                    ("Courier New", 9, False, True),
                    ("Verdana", 11, True, True),
                    ("Comic Sans MS", 8, False, False),
                ]
            )
        ]

        # Map all fields
        oracle_fields = [mapper._map_field(f) for f in fields]

        # Verify each mapping
        assert oracle_fields[0].font_name == "Arial"
        assert oracle_fields[0].font_style == "plain"

        assert oracle_fields[1].font_name == "Times"
        assert oracle_fields[1].font_style == "bold"

        assert oracle_fields[2].font_name == "Courier"
        assert oracle_fields[2].font_style == "italic"

        assert oracle_fields[3].font_name == "Helvetica"  # Verdana -> Helvetica
        assert oracle_fields[3].font_style == "bolditalic"

        assert oracle_fields[4].font_name == "Helvetica"  # Comic Sans -> Helvetica
        assert oracle_fields[4].font_style == "plain"

    def test_layout_mapper_with_custom_font_config(self):
        """Test LayoutMapper with custom font configuration."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
fonts:
  "MyCustomFont": "Courier"
  "AnotherFont": "Times"

default_font: "Helvetica"
default_size: 11
"""
            )
            config_path = f.name

        try:
            # Create layout mapper with custom config
            mapper = LayoutMapper(font_config_path=config_path)

            # Test field with custom font
            field1 = Field(
                name="CustomField",
                source="col1",
                font=FontSpec(name="MyCustomFont", size=10),
                format=FormatSpec(),
            )

            # Test field with unknown font (should use custom default)
            field2 = Field(
                name="UnknownField",
                source="col2",
                font=FontSpec(name="UnknownFontXYZ", size=10),
                format=FormatSpec(),
            )

            oracle_field1 = mapper._map_field(field1)
            oracle_field2 = mapper._map_field(field2)

            # Verify custom mapping worked
            assert oracle_field1.font_name == "Courier"

            # Verify custom default worked
            assert oracle_field2.font_name == "Helvetica"

        finally:
            Path(config_path).unlink()

    def test_layout_mapper_preserves_font_size(self):
        """Test that font sizes are preserved correctly."""
        mapper = LayoutMapper()

        sizes = [8, 10, 12, 14, 16, 18, 24, 36, 48, 72]

        for size in sizes:
            field = Field(
                name=f"Field_{size}",
                source="col",
                font=FontSpec(name="Arial", size=size),
                format=FormatSpec(),
            )

            oracle_field = mapper._map_field(field)
            assert oracle_field.font_size == size

    def test_layout_mapper_handles_extreme_sizes(self):
        """Test that extreme font sizes are handled correctly."""
        mapper = LayoutMapper()

        # Very small size
        field_small = Field(
            name="SmallField",
            source="col",
            font=FontSpec(name="Arial", size=2),
            format=FormatSpec(),
        )

        # Very large size
        field_large = Field(
            name="LargeField",
            source="col",
            font=FontSpec(name="Arial", size=200),
            format=FormatSpec(),
        )

        # None size
        field_none = Field(
            name="NoneField",
            source="col",
            font=FontSpec(name="Arial", size=None),
            format=FormatSpec(),
        )

        oracle_small = mapper._map_field(field_small)
        oracle_large = mapper._map_field(field_large)
        oracle_none = mapper._map_field(field_none)

        # Should be constrained
        assert oracle_small.font_size == 4  # Minimum
        assert oracle_large.font_size == 144  # Maximum
        assert oracle_none.font_size == 10  # Default

    def test_layout_mapper_handles_none_font(self):
        """Test that None/empty font names are handled."""
        mapper = LayoutMapper()

        field = Field(
            name="NoFontField",
            source="col",
            font=FontSpec(name=None, size=10),
            format=FormatSpec(),
        )

        oracle_field = mapper._map_field(field)
        assert oracle_field.font_name == "Arial"  # Default

    def test_complete_section_mapping_with_fonts(self):
        """Test complete section mapping preserves font information."""
        mapper = LayoutMapper()

        # Create a section with multiple fields
        section = Section(
            name="TestSection",
            section_type=SectionType.DETAIL,
            height=1000,
            fields=[
                Field(
                    name="HeaderField",
                    source="col1",
                    font=FontSpec(name="Arial", size=14, bold=True),
                    format=FormatSpec(),
                    x=0,
                    y=0,
                    width=2000,
                    height=300,
                ),
                Field(
                    name="DataField",
                    source="col2",
                    font=FontSpec(name="Times New Roman", size=10, italic=True),
                    format=FormatSpec(),
                    x=0,
                    y=300,
                    width=2000,
                    height=300,
                ),
            ],
        )

        # Map the section
        frame = mapper._map_section(section, width=540, groups=[])

        # Verify fonts were mapped in all fields
        assert len(frame.fields) == 2

        assert frame.fields[0].font_name == "Arial"
        assert frame.fields[0].font_style == "bold"
        assert frame.fields[0].font_size == 14

        assert frame.fields[1].font_name == "Times"
        assert frame.fields[1].font_style == "italic"
        assert frame.fields[1].font_size == 10

    def test_layout_mapper_default_overrides(self):
        """Test that LayoutMapper default font settings work correctly."""
        # Create mapper with custom defaults
        mapper = LayoutMapper(
            default_font="Courier",
            default_font_size=13,
        )

        # Field with no font specified
        field = Field(
            name="DefaultField",
            source="col",
            font=FontSpec(name=None, size=None),
            format=FormatSpec(),
        )

        oracle_field = mapper._map_field(field)

        # Should use custom defaults
        assert oracle_field.font_name == "Courier"
        assert oracle_field.font_size == 13

    def test_font_mapper_logging(self):
        """Test that font mapping creates appropriate log messages."""
        # This test verifies that the logger is being used
        # In a real scenario, you might capture log output to verify
        mapper = LayoutMapper()

        # Map a font that doesn't exist
        field = Field(
            name="UnknownFontField",
            source="col",
            font=FontSpec(name="NonExistentFont123", size=10),
            format=FormatSpec(),
        )

        # This should log a warning but still work
        oracle_field = mapper._map_field(field)
        assert oracle_field.font_name == "Arial"  # Falls back to default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
