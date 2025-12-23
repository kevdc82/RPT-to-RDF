"""
Unit tests for FontMapper.

Tests font mapping from Crystal Reports to Oracle Reports compatible fonts.
"""

import tempfile
from pathlib import Path

import pytest

from src.transformation.font_mapper import FontMapper


class TestFontMapperBasic:
    """Test basic font mapping functionality."""

    def test_default_initialization(self):
        """Test FontMapper initializes with default settings."""
        mapper = FontMapper()
        assert mapper.default_font == "Arial"
        assert mapper.default_size == 10
        assert len(mapper.font_map) > 0

    def test_custom_defaults(self):
        """Test FontMapper with custom default font and size."""
        mapper = FontMapper(default_font="Helvetica", default_size=12)
        assert mapper.default_font == "Helvetica"
        assert mapper.default_size == 12

    def test_exact_font_match(self):
        """Test exact font name matching."""
        mapper = FontMapper()
        assert mapper.map_font("Arial") == "Arial"
        assert mapper.map_font("Times New Roman") == "Times"
        assert mapper.map_font("Courier New") == "Courier"

    def test_case_insensitive_match(self):
        """Test case-insensitive font matching."""
        mapper = FontMapper()
        assert mapper.map_font("arial") == "Arial"
        assert mapper.map_font("VERDANA") == "Helvetica"
        assert mapper.map_font("times new roman") == "Times"

    def test_partial_font_match(self):
        """Test partial font name matching."""
        mapper = FontMapper()
        # Should match "Arial" even with extra text
        result = mapper.map_font("Arial Unicode MS")
        assert result == "Arial"

    def test_unknown_font_fallback(self):
        """Test fallback to default font for unknown fonts."""
        mapper = FontMapper()
        assert mapper.map_font("UnknownFont123") == "Arial"
        assert mapper.map_font("SomeWeirdFont") == "Arial"

    def test_empty_font_fallback(self):
        """Test fallback to default font for empty/None font."""
        mapper = FontMapper()
        assert mapper.map_font("") == "Arial"
        assert mapper.map_font(None) == "Arial"


class TestFontMapperStyle:
    """Test font style mapping."""

    def test_plain_style(self):
        """Test plain (no bold, no italic) style."""
        mapper = FontMapper()
        assert mapper.map_font_style(bold=False, italic=False) == "plain"

    def test_bold_style(self):
        """Test bold style."""
        mapper = FontMapper()
        assert mapper.map_font_style(bold=True, italic=False) == "bold"

    def test_italic_style(self):
        """Test italic style."""
        mapper = FontMapper()
        assert mapper.map_font_style(bold=False, italic=True) == "italic"

    def test_bolditalic_style(self):
        """Test bold + italic style."""
        mapper = FontMapper()
        assert mapper.map_font_style(bold=True, italic=True) == "bolditalic"

    def test_underline_ignored(self):
        """Test that underline doesn't affect style string (tracked separately)."""
        mapper = FontMapper()
        # Underline is tracked but doesn't change the style string
        assert mapper.map_font_style(bold=False, italic=False, underline=True) == "plain"
        assert mapper.map_font_style(bold=True, italic=False, underline=True) == "bold"


class TestFontMapperSize:
    """Test font size mapping."""

    def test_normal_size(self):
        """Test normal font sizes."""
        mapper = FontMapper()
        assert mapper.map_font_size(10) == 10
        assert mapper.map_font_size(12) == 12
        assert mapper.map_font_size(24) == 24

    def test_none_size(self):
        """Test None size returns default."""
        mapper = FontMapper()
        assert mapper.map_font_size(None) == 10

    def test_zero_size(self):
        """Test zero or negative size returns default."""
        mapper = FontMapper()
        assert mapper.map_font_size(0) == 10
        assert mapper.map_font_size(-5) == 10

    def test_too_small_size(self):
        """Test very small sizes are constrained to minimum."""
        mapper = FontMapper()
        assert mapper.map_font_size(1) == 4
        assert mapper.map_font_size(3) == 4

    def test_too_large_size(self):
        """Test very large sizes are constrained to maximum."""
        mapper = FontMapper()
        assert mapper.map_font_size(200) == 144
        assert mapper.map_font_size(500) == 144

    def test_boundary_sizes(self):
        """Test boundary size values."""
        mapper = FontMapper()
        assert mapper.map_font_size(4) == 4  # Minimum
        assert mapper.map_font_size(144) == 144  # Maximum


class TestFontMapperGetFontInfo:
    """Test get_font_info comprehensive method."""

    def test_complete_font_info(self):
        """Test getting complete font information."""
        mapper = FontMapper()
        info = mapper.get_font_info(
            crystal_font="Times New Roman",
            crystal_size=14,
            bold=True,
            italic=False,
            underline=True,
        )

        assert info["oracle_font"] == "Times"
        assert info["oracle_size"] == 14
        assert info["oracle_style"] == "bold"
        assert info["underline"] is True

    def test_font_info_with_defaults(self):
        """Test getting font info with None values."""
        mapper = FontMapper()
        info = mapper.get_font_info(
            crystal_font=None,
            crystal_size=None,
            bold=False,
            italic=False,
        )

        assert info["oracle_font"] == "Arial"
        assert info["oracle_size"] == 10
        assert info["oracle_style"] == "plain"

    def test_font_info_bolditalic(self):
        """Test font info with bold and italic."""
        mapper = FontMapper()
        info = mapper.get_font_info(
            crystal_font="Verdana",
            crystal_size=11,
            bold=True,
            italic=True,
        )

        assert info["oracle_font"] == "Helvetica"
        assert info["oracle_size"] == 11
        assert info["oracle_style"] == "bolditalic"


class TestFontMapperConfig:
    """Test configuration file loading."""

    def test_load_custom_config(self):
        """Test loading custom font mappings from YAML."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
fonts:
  "Custom Font": "Helvetica"
  "Another Font": "Times"

default_font: "Courier"
default_size: 11
"""
            )
            config_path = f.name

        try:
            mapper = FontMapper(config_path=config_path)

            # Check custom mappings loaded
            assert mapper.map_font("Custom Font") == "Helvetica"
            assert mapper.map_font("Another Font") == "Times"

            # Check defaults updated
            assert mapper.default_font == "Courier"
            assert mapper.default_size == 11

            # Check that default mappings are still there
            assert mapper.map_font("Arial") == "Arial"

        finally:
            # Clean up temp file
            Path(config_path).unlink()

    def test_missing_config_file(self):
        """Test that missing config file doesn't crash."""
        mapper = FontMapper(config_path="/nonexistent/path/to/config.yaml")
        # Should still work with defaults
        assert mapper.map_font("Arial") == "Arial"
        assert mapper.default_font == "Arial"

    def test_empty_config_file(self):
        """Test empty config file handling."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_path = f.name

        try:
            mapper = FontMapper(config_path=config_path)
            # Should still work with defaults
            assert mapper.map_font("Arial") == "Arial"
        finally:
            Path(config_path).unlink()


class TestFontMapperCustomMappings:
    """Test runtime custom mapping additions."""

    def test_add_custom_mapping(self):
        """Test adding custom font mapping at runtime."""
        mapper = FontMapper()

        # Add a custom mapping
        mapper.add_custom_mapping("MyFont", "Courier")

        # Verify it works
        assert mapper.map_font("MyFont") == "Courier"

    def test_override_existing_mapping(self):
        """Test overriding an existing font mapping."""
        mapper = FontMapper()

        # Override Arial to map to Helvetica
        mapper.add_custom_mapping("Arial", "Helvetica")

        assert mapper.map_font("Arial") == "Helvetica"

    def test_get_all_mappings(self):
        """Test retrieving all current mappings."""
        mapper = FontMapper()
        mappings = mapper.get_all_mappings()

        assert isinstance(mappings, dict)
        assert "Arial" in mappings
        assert "Times New Roman" in mappings
        assert len(mappings) > 0

        # Verify it's a copy (modifying it doesn't affect mapper)
        mappings["TestFont"] = "TestValue"
        assert "TestFont" not in mapper.font_map


class TestFontMapperCommonFonts:
    """Test mapping of common Crystal Reports fonts."""

    def test_sans_serif_fonts(self):
        """Test sans-serif fonts map correctly."""
        mapper = FontMapper()

        sans_serif_fonts = [
            ("Arial", "Arial"),
            ("Verdana", "Helvetica"),
            ("Tahoma", "Helvetica"),
            ("Calibri", "Helvetica"),
            ("Trebuchet MS", "Helvetica"),
            ("Century Gothic", "Helvetica"),
        ]

        for crystal, expected in sans_serif_fonts:
            assert mapper.map_font(crystal) == expected, f"Failed for {crystal}"

    def test_serif_fonts(self):
        """Test serif fonts map correctly."""
        mapper = FontMapper()

        serif_fonts = [
            ("Times New Roman", "Times"),
            ("Georgia", "Times"),
            ("Garamond", "Times"),
            ("Cambria", "Times"),
            ("Palatino Linotype", "Times"),
        ]

        for crystal, expected in serif_fonts:
            assert mapper.map_font(crystal) == expected, f"Failed for {crystal}"

    def test_monospace_fonts(self):
        """Test monospace fonts map correctly."""
        mapper = FontMapper()

        monospace_fonts = [
            ("Courier New", "Courier"),
            ("Courier", "Courier"),
            ("Consolas", "Courier"),
            ("Lucida Console", "Courier"),
        ]

        for crystal, expected in monospace_fonts:
            assert mapper.map_font(crystal) == expected, f"Failed for {crystal}"

    def test_symbol_fonts(self):
        """Test symbol fonts map correctly."""
        mapper = FontMapper()

        assert mapper.map_font("Symbol") == "Symbol"
        assert mapper.map_font("Wingdings") == "Symbol"


class TestFontMapperEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_font_names(self):
        """Test handling of unicode in font names."""
        mapper = FontMapper()

        # Should handle unicode gracefully and fall back to default
        result = mapper.map_font("微软雅黑")  # Microsoft YaHei in Chinese
        assert result == "Arial"

    def test_very_long_font_name(self):
        """Test handling of very long font names."""
        mapper = FontMapper()

        long_name = "A" * 500
        result = mapper.map_font(long_name)
        assert result == "Arial"

    def test_special_characters_in_font_name(self):
        """Test font names with special characters."""
        mapper = FontMapper()

        # Should handle gracefully
        result = mapper.map_font("Font@#$%^&*()")
        assert result == "Arial"

    def test_whitespace_font_name(self):
        """Test font name with only whitespace."""
        mapper = FontMapper()

        result = mapper.map_font("   ")
        # Whitespace-only should be treated as empty
        assert result == "Arial"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
