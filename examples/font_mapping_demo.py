#!/usr/bin/env python3
"""
Font Mapping Demonstration Script

This script demonstrates how the FontMapper works to convert Crystal Reports
fonts to Oracle Reports compatible fonts.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformation.font_mapper import FontMapper


def print_separator():
    """Print a separator line."""
    print("-" * 70)


def demo_basic_mapping():
    """Demonstrate basic font mapping."""
    print("\n=== BASIC FONT MAPPING ===\n")

    mapper = FontMapper()

    fonts_to_test = [
        "Arial",
        "Times New Roman",
        "Courier New",
        "Verdana",
        "Tahoma",
        "Georgia",
        "Calibri",
        "Comic Sans MS",
    ]

    print("Crystal Font              -> Oracle Font")
    print_separator()

    for font in fonts_to_test:
        oracle_font = mapper.map_font(font)
        print(f"{font:25} -> {oracle_font}")


def demo_font_styles():
    """Demonstrate font style mapping."""
    print("\n\n=== FONT STYLE MAPPING ===\n")

    mapper = FontMapper()

    style_combinations = [
        (False, False, False, "Regular text"),
        (True, False, False, "Bold text"),
        (False, True, False, "Italic text"),
        (True, True, False, "Bold + Italic text"),
        (False, False, True, "Underlined text"),
        (True, False, True, "Bold + Underlined text"),
    ]

    print("Style Description             -> Oracle Style")
    print_separator()

    for bold, italic, underline, description in style_combinations:
        style = mapper.map_font_style(bold, italic, underline)
        underline_note = " (underline tracked separately)" if underline else ""
        print(f"{description:30} -> {style}{underline_note}")


def demo_font_sizes():
    """Demonstrate font size mapping and constraints."""
    print("\n\n=== FONT SIZE MAPPING ===\n")

    mapper = FontMapper()

    sizes_to_test = [
        (None, "None (uses default)"),
        (0, "Zero (invalid)"),
        (1, "1pt (too small)"),
        (8, "8pt (small)"),
        (10, "10pt (normal)"),
        (14, "14pt (medium)"),
        (24, "24pt (large)"),
        (72, "72pt (very large)"),
        (200, "200pt (too large)"),
    ]

    print("Input Size                    -> Oracle Size")
    print_separator()

    for size, description in sizes_to_test:
        oracle_size = mapper.map_font_size(size)
        print(f"{description:30} -> {oracle_size}pt")


def demo_complete_font_info():
    """Demonstrate getting complete font information."""
    print("\n\n=== COMPLETE FONT INFO ===\n")

    mapper = FontMapper()

    test_cases = [
        ("Arial", 10, False, False, False, "Plain Arial 10pt"),
        ("Times New Roman", 14, True, False, False, "Bold Times 14pt"),
        ("Verdana", 12, False, True, False, "Italic Verdana 12pt"),
        ("Georgia", 16, True, True, True, "Bold Italic Underlined Georgia 16pt"),
    ]

    print("Input Font Info                                    -> Oracle Font Info")
    print_separator()

    for font, size, bold, italic, underline, description in test_cases:
        info = mapper.get_font_info(font, size, bold, italic, underline)
        output = f"{info['oracle_font']} {info['oracle_size']}pt {info['oracle_style']}"
        if info['underline']:
            output += " (underlined)"
        print(f"{description:50} -> {output}")


def demo_unknown_fonts():
    """Demonstrate handling of unknown fonts."""
    print("\n\n=== UNKNOWN FONT HANDLING ===\n")

    mapper = FontMapper()

    unknown_fonts = [
        "UnknownFont123",
        "CustomBusinessFont",
        "MySpecialFont",
        "",
        None,
    ]

    print("Unknown Font                  -> Oracle Font (fallback)")
    print_separator()

    for font in unknown_fonts:
        display_font = repr(font) if font is None or font == "" else font
        oracle_font = mapper.map_font(font)
        print(f"{display_font:30} -> {oracle_font}")


def demo_custom_mappings():
    """Demonstrate adding custom font mappings at runtime."""
    print("\n\n=== CUSTOM FONT MAPPINGS ===\n")

    mapper = FontMapper()

    # Add custom mappings
    mapper.add_custom_mapping("CompanyFont", "Helvetica")
    mapper.add_custom_mapping("ReportFont", "Times")

    print("Added custom mappings:")
    print("  CompanyFont -> Helvetica")
    print("  ReportFont  -> Times")
    print()

    # Test custom mappings
    print("Testing custom mappings:")
    print_separator()
    print(f"CompanyFont -> {mapper.map_font('CompanyFont')}")
    print(f"ReportFont  -> {mapper.map_font('ReportFont')}")


def demo_case_sensitivity():
    """Demonstrate case-insensitive matching."""
    print("\n\n=== CASE SENSITIVITY ===\n")

    mapper = FontMapper()

    font_variations = [
        "Arial",
        "arial",
        "ARIAL",
        "ArIaL",
        "Times New Roman",
        "times new roman",
        "TIMES NEW ROMAN",
    ]

    print("Font Name (various cases)     -> Oracle Font")
    print_separator()

    for font in font_variations:
        oracle_font = mapper.map_font(font)
        print(f"{font:30} -> {oracle_font}")


def main():
    """Run all demonstrations."""
    print("=" * 70)
    print("FONT MAPPER DEMONSTRATION")
    print("=" * 70)

    # Run all demos
    demo_basic_mapping()
    demo_font_styles()
    demo_font_sizes()
    demo_complete_font_info()
    demo_unknown_fonts()
    demo_custom_mappings()
    demo_case_sensitivity()

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()

    # Summary
    print("\nKEY POINTS:")
    print("  - Crystal fonts are mapped to Oracle-compatible fonts")
    print("  - Standard Oracle fonts: Arial, Helvetica, Times, Courier, Symbol")
    print("  - Font styles: plain, bold, italic, bolditalic")
    print("  - Font sizes are validated (min: 4pt, max: 144pt)")
    print("  - Unknown fonts fall back to default (Arial)")
    print("  - Font mappings can be customized via YAML config or at runtime")
    print()


if __name__ == "__main__":
    main()
