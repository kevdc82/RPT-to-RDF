# HTML Preview Generator - Implementation Summary

## Overview

Added an HTML preview generator feature to the RPT-to-RDF converter that creates visual representations of converted reports without requiring Oracle Reports to be installed.

## Files Created

### 1. `/src/generation/html_preview.py`
Main implementation file containing the `HTMLPreviewGenerator` class.

**Key Methods:**
- `generate(report: ReportModel, output_path: Path)` - Generate preview from ReportModel
- `generate_from_xml(xml_path: Path, output_path: Path)` - Generate preview from Oracle XML
- `_render_section(section: Section)` - Render individual report sections
- `_render_field(field: Field)` - Render field elements with styling
- `_generate_css()` - Generate complete CSS stylesheet

**Features:**
- Visual layout with approximate field positioning
- Color-coded fields by type (database, formula, parameter, special)
- Section labels and boundaries
- Metadata display (complexity, counts, page settings)
- Conversion warnings and notes
- Hover tooltips showing field sources
- Print-ready CSS styles

## Files Modified

### 1. `/src/main.py`
Added new CLI command `preview` with the following options:
- `INPUT_PATH` - Required: Path to XML file (Crystal or Oracle)
- `--output, -o` - Optional: Custom output path (default: input_name_preview.html)
- `--from-xml` - Flag: Generate from Oracle XML instead of Crystal XML

### 2. `/README.md`
Updated documentation:
- Added "HTML Preview" to features list
- Added `preview` command to CLI commands section
- Created dedicated "Preview Command" section with:
  - Usage examples
  - Feature descriptions
  - Field color coding guide

## Usage Examples

### Generate preview from Crystal Reports XML
```bash
python -m src.main preview ./temp/SportsTeams.xml
```

### Generate preview from Oracle Reports XML
```bash
python -m src.main preview ./output/SportsTeams.xml --from-xml
```

### Specify custom output path
```bash
python -m src.main preview ./temp/report.xml -o ./previews/report.html
```

## HTML Preview Features

### Visual Layout
- Page dimensions based on report metadata (Letter/Legal, Portrait/Landscape)
- Margin calculations from report settings
- Section boundaries with dashed borders
- Approximate field positioning using absolute positioning

### Section Rendering
- Color-coded section backgrounds:
  - Report Header: Light gray (#f8f9fa)
  - Page Header: Gray (#e9ecef)
  - Group Header/Footer: Darker gray (#dee2e6)
  - Detail: White
  - Page Footer: Gray (#e9ecef)
  - Report Footer: Light gray (#f8f9fa)
- Section labels positioned on the left margin
- Section type and group number display

### Field Display
- Database fields: `{Table.Column}` in blue (#0066cc)
- Formula fields: `@FormulaName` in orange (#cc6600)
- Parameter fields: `?ParameterName` in green (#009900)
- Special fields: Field names in gray (#666666, italic)

### Font and Styling
- Font family, size, and weight from field metadata
- Bold, italic, underline support
- Text alignment (left, center, right)
- Vertical alignment (top, middle, bottom)
- Border and background color support

### Metadata Section
- Report title and author
- Paper size and orientation
- Margin settings
- Complexity score with color coding:
  - Green (1-3): Simple
  - Orange (4-6): Medium
  - Red (7-10): Complex
- Field, formula, parameter, section, and group counts

### Warnings and Notes
- Unsupported features displayed in yellow alert box
- Conversion notes displayed separately
- Both sections collapsible and clearly marked

### Interactive Features
- Hover over fields to see source name in tooltip
- Field highlighting on hover (blue border + light background)
- Responsive layout within container

### Print Support
- CSS print media queries
- Hides preview header, footer, and warnings when printing
- Removes section labels for clean printout
- Maintains report layout for documentation

## Technical Implementation

### CSS Grid/Absolute Positioning
Uses absolute positioning within sections to approximate Crystal Reports layout:
- Fields positioned using `left`, `top`, `width`, `height` in pixels
- Sections use relative positioning as containers
- Report content centered within page boundaries

### HTML Structure
```html
<div class="preview-container">
  <div class="preview-header">
    <!-- Report metadata -->
  </div>
  <div class="warnings">
    <!-- Unsupported features & notes -->
  </div>
  <div class="report-page">
    <div class="report-content">
      <div class="section section-reportheader">
        <div class="section-label">Report Header</div>
        <div class="section-content">
          <div class="field field-database">
            {Table.Column}
          </div>
        </div>
      </div>
      <!-- More sections -->
    </div>
  </div>
  <div class="preview-footer">
    <!-- Disclaimer text -->
  </div>
</div>
```

### Two Preview Modes

1. **Crystal XML Mode** (default)
   - Parses Crystal Reports XML using CrystalParser
   - Builds complete ReportModel with all metadata
   - Generates detailed preview with full field information
   - Shows exact field positions, fonts, and styling

2. **Oracle XML Mode** (`--from-xml`)
   - Parses Oracle Reports XML directly
   - Shows structural layout (frames and fields)
   - Simplified view focused on Oracle format
   - Useful for verifying Oracle XML generation

## Testing

Tested with the following reports:
- ✅ SportsTeams.xml - Basic report with header and detail sections
- ✅ ColourPaletteSampler.xml - Report with multiple sections
- ✅ SportsTeams.xml (Oracle) - Oracle XML structural view

## Browser Compatibility

The generated HTML uses standard CSS features compatible with:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Internet Explorer 11+ (with graceful degradation)

## Limitations

- Field positions are approximate (based on XML coordinates)
- Actual data values are not shown (placeholders only)
- Complex Crystal formulas shown as formula names
- Subreports not rendered (shown as references)
- Some advanced formatting may not be replicated exactly

## Future Enhancements

Potential improvements:
1. Sample data injection for more realistic previews
2. Side-by-side Crystal vs. Oracle comparison view
3. Interactive field editing/repositioning
4. Export to PDF functionality
5. Batch preview generation for multiple reports
6. Diff view showing changes during conversion
7. Formula expansion/preview in tooltips

## Benefits

1. **Visual Verification**: Quickly verify report layout without Oracle Reports
2. **Documentation**: Create printable documentation of report structure
3. **Debugging**: Identify layout issues during conversion
4. **Communication**: Share visual previews with stakeholders
5. **Testing**: Verify conversion quality without full Oracle setup
6. **Batch Review**: Generate previews for entire report libraries
