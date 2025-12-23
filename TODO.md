# RPT to RDF Converter - TODO

This document tracks remaining work items and future enhancements for the Crystal Reports to Oracle Reports converter.

## High Priority

### Data Model Generation (Critical)
- [ ] **Populate `<data>` section in Oracle XML** - Currently generates empty `<data/>` section
  - Extract SQL queries from Crystal Reports XML
  - Convert Crystal database connections to Oracle connections
  - Generate proper `<dataSource>` and `<group>` elements
  - Map Crystal field references to Oracle column names

### Oracle Reports RDF Generation
- [ ] **Test with actual Oracle Reports 12c installation**
  - Set up Oracle Reports 12c in Docker or VM
  - Test rwconverter with generated Oracle XML
  - Validate generated RDF files can be opened in Oracle Reports Builder
  - Document any required XML adjustments

### Formula Translation Improvements
- [ ] **Expand formula function mappings**
  - Add more Crystal-to-PL/SQL function translations
  - Handle nested IIF statements → CASE WHEN conversion
  - Support running totals → Oracle analytic functions
  - Handle WhilePrintingRecords formulas

## Medium Priority

### Enhanced Report Features
- [ ] **Subreport handling**
  - Extract and convert subreports
  - Handle subreport parameters and linking
  - Support nested subreports (up to 2 levels)

- [ ] **Chart and graph support**
  - Extract chart definitions from Crystal Reports
  - Map to Oracle Reports chart objects
  - Handle chart data series and formatting

- [ ] **Cross-tab reports**
  - Parse cross-tab structure from Crystal XML
  - Generate Oracle Reports matrix/cross-tab equivalent

### Layout Improvements
- [ ] **Precise coordinate conversion**
  - Crystal uses twips (1/1440 inch)
  - Oracle uses points or inches
  - Implement accurate conversion: `oracle_points = crystal_twips / 20`

- [ ] **Font mapping**
  - Map Crystal font names to Oracle-compatible fonts
  - Handle font size and style conversion

- [ ] **Conditional formatting**
  - Convert Crystal conditional formatting to Oracle format triggers
  - Handle suppress conditions

### Testing
- [ ] **Expand test suite**
  - Add unit tests for formula translator
  - Add integration tests for full pipeline
  - Create test fixtures with various report types
  - Add regression tests for edge cases

- [ ] **Validation framework**
  - Compare Crystal and Oracle report output
  - Visual PDF comparison
  - Data output comparison (CSV)

## Low Priority

### Performance Optimization
- [ ] **Parallel processing improvements**
  - Optimize batch rwconverter calls
  - Better progress reporting for large batches
  - Memory optimization for large reports

### Documentation
- [ ] **API documentation**
  - Document internal classes and methods
  - Add docstrings to all public functions
  - Generate API reference with Sphinx

- [ ] **User guide**
  - Step-by-step tutorial for common scenarios
  - Video walkthrough of conversion process
  - FAQ section

### Additional Features
- [ ] **Report preview**
  - Generate HTML preview of converted reports
  - Show side-by-side comparison with original

- [ ] **Conversion rules customization**
  - Allow users to define custom formula mappings
  - Support custom type mappings via config
  - Plugin system for custom transformations

- [ ] **Batch scheduling**
  - Support for scheduled batch conversions
  - Email notifications on completion
  - Integration with CI/CD pipelines

## Technical Debt

### Code Quality
- [ ] **Type hints**
  - Add complete type hints to all modules
  - Configure mypy for strict type checking

- [ ] **Error handling**
  - Improve error messages with actionable guidance
  - Add error codes for common failures
  - Better stack trace handling in logs

### Infrastructure
- [ ] **CI/CD pipeline**
  - Set up GitHub Actions for automated testing
  - Add linting checks (black, isort, flake8)
  - Automated releases

- [ ] **Docker improvements**
  - Multi-stage build for smaller image
  - Add health checks
  - Support for ARM64 (Apple Silicon)

## Completed

### Phase 1: Foundation ✅
- [x] Project structure setup
- [x] Configuration management
- [x] Logging infrastructure
- [x] Error handling framework
- [x] CLI skeleton

### Phase 2: Extraction ✅
- [x] Java RptToXml wrapper
- [x] Docker-based extraction (cross-platform)
- [x] Fixed Crystal SDK path resolution issue
- [x] Batch extraction with wrapper script

### Phase 3: Basic Transformation ✅
- [x] Type mapper (Crystal → Oracle types)
- [x] Basic formula translator
- [x] Parameter mapper
- [x] Layout mapper (sections → frames)

### Phase 4: Generation ✅
- [x] Oracle Reports XML generator
- [x] rwconverter wrapper
- [x] `--skip-rdf` option for XML-only output

### Phase 5: Data Migration ✅
- [x] MDB extractor utility
- [x] Oracle DDL generation from MDB
- [x] CSV export
- [x] SQL*Loader control file generation
- [x] INSERT statement generation
- [x] Schema extraction from Crystal Reports XML

### Phase 6: Documentation ✅
- [x] Comprehensive README
- [x] Docker documentation
- [x] CLI help text
- [x] TODO tracking

---

## Contributing

If you'd like to contribute to any of these items:

1. Check if an issue exists for the item
2. Create an issue if one doesn't exist
3. Fork the repository
4. Create a feature branch
5. Submit a pull request

## Notes

- Priority levels may change based on user feedback
- Items marked as "Critical" block production use
- "Medium" items enhance functionality but aren't blocking
- "Low" items are nice-to-have improvements
