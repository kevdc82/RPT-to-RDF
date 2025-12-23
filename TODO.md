# RPT to RDF Converter - TODO

This document tracks remaining work items and future enhancements for the Crystal Reports to Oracle Reports converter.

## High Priority

### Oracle Reports RDF Generation
- [ ] **Test with actual Oracle Reports 12c installation**
  - Set up Oracle Reports 12c in Docker or VM
  - Test rwconverter with generated Oracle XML
  - Validate generated RDF files can be opened in Oracle Reports Builder
  - Document any required XML adjustments

## Medium Priority

### Enhanced Report Features

- [ ] **Chart and graph support**
  - Extract chart definitions from Crystal Reports
  - Map to Oracle Reports chart objects
  - Handle chart data series and formatting

- [ ] **Cross-tab reports**
  - Parse cross-tab structure from Crystal XML
  - Generate Oracle Reports matrix/cross-tab equivalent

### Testing
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

### Phase 7: Enhanced Transformation ✅
- [x] Populate `<data>` section in Oracle XML
- [x] SQL query generation from table/field info
- [x] DataSource, group, dataItem element creation
- [x] Expanded formula function mappings (StrCmp, ProperCase, DatePart, Timer, etc.)
- [x] Running totals → SUM() OVER() conversion
- [x] Coordinate conversion (twips → points)
- [x] Font mapping with YAML config
- [x] Conditional formatting → format triggers
- [x] Type hints added to modules
- [x] Comprehensive unit test suite
- [x] HTML preview generator

### Phase 8: Formula & Subreport Enhancements ✅
- [x] CurrentDate, CurrentTime, Timer keyword functions
- [x] Nested function conversion (Left → SUBSTR inside Upper/Trim)
- [x] WhilePrintingRecords directive handling
- [x] Subreport transformation (TransformedSubreport model)
- [x] Subreport XML generation with parameter links
- [x] SRW.RUN_REPORT helper procedure stubs

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
