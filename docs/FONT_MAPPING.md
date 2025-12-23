# Font Mapping Guide

## Overview

The Font Mapper component handles the conversion of Crystal Reports fonts to Oracle Reports compatible fonts. This is necessary because Oracle Reports supports a limited set of standard fonts, while Crystal Reports may use any system font.

## Supported Oracle Fonts

Oracle Reports supports these standard fonts:
- **Arial** - Sans-serif font
- **Helvetica** - Sans-serif font
- **Times** - Serif font
- **Courier** - Monospace font
- **Symbol** - Special characters/symbols

## Font Mapping Strategy

### Sans-Serif Fonts
These Crystal fonts map to **Arial** or **Helvetica**:
- Arial → Arial
- Verdana → Helvetica
- Tahoma → Helvetica
- Calibri → Helvetica
- Trebuchet MS → Helvetica
- Century Gothic → Helvetica
- Franklin Gothic → Helvetica
- Comic Sans MS → Helvetica
- Lucida Sans → Helvetica

### Serif Fonts
These Crystal fonts map to **Times**:
- Times New Roman → Times
- Times → Times
- Georgia → Times
- Garamond → Times
- Cambria → Times
- Palatino → Times
- Book Antiqua → Times

### Monospace Fonts
These Crystal fonts map to **Courier**:
- Courier New → Courier
- Courier → Courier
- Consolas → Courier
- Lucida Console → Courier
- Monaco → Courier

### Symbol Fonts
These Crystal fonts map to **Symbol**:
- Symbol → Symbol
- Wingdings → Symbol
- Webdings → Symbol

## Font Styles

Oracle Reports supports four font styles:
- **plain** - Normal text
- **bold** - Bold text
- **italic** - Italic text
- **bolditalic** - Both bold and italic

Note: Underline is tracked separately but doesn't affect the style string in Oracle Reports.

## Font Sizes

- Font sizes are preserved from Crystal Reports (1:1 mapping)
- Sizes are constrained to reasonable bounds:
  - Minimum: 4 points
  - Maximum: 144 points
- Invalid sizes (None, 0, negative) use the default size (10pt)

## Configuration

### YAML Configuration File

You can customize font mappings using `config/font_mappings.yaml`:

```yaml
# Font mappings from Crystal to Oracle
fonts:
  "My Custom Font": "Helvetica"
  "Company Font": "Times"

# Default font for unknown fonts
default_font: Arial

# Default font size
default_size: 10
```

### Programmatic Configuration

You can also add custom mappings at runtime:

```python
from src.transformation.font_mapper import FontMapper

mapper = FontMapper()
mapper.add_custom_mapping("CustomFont", "Courier")
```

## Usage

### Using FontMapper Directly

```python
from src.transformation.font_mapper import FontMapper

# Initialize mapper
mapper = FontMapper()

# Map a font name
oracle_font = mapper.map_font("Times New Roman")  # Returns "Times"

# Map font style
style = mapper.map_font_style(bold=True, italic=False)  # Returns "bold"

# Map font size
size = mapper.map_font_size(14)  # Returns 14

# Get complete font info
info = mapper.get_font_info(
    crystal_font="Verdana",
    crystal_size=12,
    bold=True,
    italic=True,
    underline=False
)
# Returns: {
#   "oracle_font": "Helvetica",
#   "oracle_size": 12,
#   "oracle_style": "bolditalic",
#   "underline": False
# }
```

### Integration with LayoutMapper

The LayoutMapper automatically uses FontMapper:

```python
from src.transformation.layout_mapper import LayoutMapper

# Create layout mapper (FontMapper is initialized internally)
mapper = LayoutMapper()

# Or with custom font config
mapper = LayoutMapper(font_config_path="config/font_mappings.yaml")

# Font mapping happens automatically during field mapping
```

## Examples

### Running the Demo

A demonstration script is provided to show font mapping in action:

```bash
python examples/font_mapping_demo.py
```

This will display:
- Basic font mappings
- Font style conversions
- Font size handling
- Complete font information
- Unknown font fallback behavior
- Custom mapping capabilities

### Example Output

```
Crystal Font              -> Oracle Font
----------------------------------------------------------------------
Arial                     -> Arial
Times New Roman           -> Times
Courier New               -> Courier
Verdana                   -> Helvetica
Tahoma                    -> Helvetica
Georgia                   -> Times
```

## Best Practices

1. **Review Font Mappings**: Before converting a report, review which fonts are used and verify the mappings are appropriate.

2. **Test Visual Appearance**: After conversion, visually compare the Crystal and Oracle reports to ensure fonts render acceptably.

3. **Document Custom Fonts**: If your organization uses custom fonts, document the mappings in `font_mappings.yaml`.

4. **Consider Font Substitution**: Some fonts may not have perfect equivalents. Be prepared to adjust layouts if font metrics differ significantly.

5. **Use Standard Fonts**: When creating new Crystal Reports that will be converted, prefer standard fonts (Arial, Times, Courier) for easier conversion.

## Troubleshooting

### Font Not Mapping Correctly

If a font isn't mapping as expected:

1. Check if the font name is spelled correctly
2. Verify the font exists in `font_mappings.yaml`
3. Check the logs for warnings about unmapped fonts
4. Add a custom mapping if needed

### Font Appears Different in Oracle

If fonts look different after conversion:

1. Verify the font size was preserved correctly
2. Check that bold/italic styles mapped properly
3. Consider that different fonts have different metrics
4. Adjust spacing/sizing in the Oracle report if needed

### Unknown Font Warnings

If you see warnings about unknown fonts:

1. Identify the Crystal font being used
2. Determine the best Oracle equivalent
3. Add a mapping to `font_mappings.yaml`
4. Re-run the conversion

## Testing

### Running Unit Tests

```bash
# Run font mapper tests
python -m pytest tests/test_font_mapper.py -v

# Run integration tests
python -m pytest tests/test_font_mapper_integration.py -v

# Run all tests with coverage
python -m pytest tests/test_font_mapper*.py --cov=src.transformation.font_mapper -v
```

### Test Coverage

The font mapper includes comprehensive tests for:
- Basic font mapping (exact, case-insensitive, partial matching)
- Font style mapping (all combinations)
- Font size mapping (normal, extreme, invalid values)
- Configuration file loading
- Custom runtime mappings
- Edge cases and error handling
- Integration with LayoutMapper

## Future Enhancements

Potential future improvements:

1. **Font Size Adjustments**: Support for scaling fonts when substituting (e.g., make Verdana 90% of original size)
2. **Font Metrics Database**: Track character widths for better layout preservation
3. **Visual Font Matching**: AI-based font matching for closest visual equivalents
4. **Custom Font Embedding**: Support for embedding custom fonts in Oracle Reports
5. **Font Usage Report**: Generate report of all fonts used and their mappings

## Related Documentation

- [Layout Mapper Documentation](./LAYOUT_MAPPER.md)
- [Oracle XML Generator Documentation](./ORACLE_XML_GENERATOR.md)
- [Configuration Guide](./CONFIGURATION.md)

## Support

For issues or questions about font mapping:
1. Check the logs for warnings and errors
2. Review the example scripts
3. Consult the test files for usage patterns
4. Create an issue with font details and expected behavior
