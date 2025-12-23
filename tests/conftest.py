"""
Pytest configuration and shared fixtures.

This file contains common fixtures used across multiple test files.
"""

from pathlib import Path

import pytest

from src.parsing.report_model import (
    DataType,
    Field,
    FontSpec,
    FormatSpec,
    Formula,
    FormulaSyntax,
    Group,
    Query,
    QueryColumn,
    Section,
    SectionType,
)
from src.transformation.formula_translator import FormulaTranslator
from src.transformation.layout_mapper import LayoutMapper
from src.transformation.type_mapper import TypeMapper


# Directory fixtures
@pytest.fixture
def test_data_dir():
    """Return the test data directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_fixtures_dir(test_data_dir):
    """Return the simple test fixtures directory."""
    return test_data_dir / "simple"


@pytest.fixture
def medium_fixtures_dir(test_data_dir):
    """Return the medium test fixtures directory."""
    return test_data_dir / "medium"


@pytest.fixture
def complex_fixtures_dir(test_data_dir):
    """Return the complex test fixtures directory."""
    return test_data_dir / "complex"


# Component fixtures
@pytest.fixture
def formula_translator():
    """Create a FormulaTranslator instance."""
    return FormulaTranslator(formula_prefix="CF_", on_unsupported="placeholder")


@pytest.fixture
def type_mapper():
    """Create a TypeMapper instance."""
    return TypeMapper()


@pytest.fixture
def layout_mapper():
    """Create a LayoutMapper instance."""
    return LayoutMapper(field_prefix="F_", coordinate_unit="points")


# Sample data fixtures
@pytest.fixture
def sample_string_formula():
    """Create a sample string formula."""
    return Formula(
        name="TestFormula",
        expression="{FirstName} & ' ' & {LastName}",
        return_type=DataType.STRING,
        syntax=FormulaSyntax.CRYSTAL,
    )


@pytest.fixture
def sample_number_formula():
    """Create a sample number formula."""
    return Formula(
        name="TotalAmount",
        expression="{Quantity} * {Price}",
        return_type=DataType.NUMBER,
        syntax=FormulaSyntax.CRYSTAL,
    )


@pytest.fixture
def sample_date_formula():
    """Create a sample date formula."""
    return Formula(
        name="CurrentDate",
        expression="CurrentDate",
        return_type=DataType.DATE,
        syntax=FormulaSyntax.CRYSTAL,
    )


@pytest.fixture
def sample_iif_formula():
    """Create a sample IIF formula."""
    return Formula(
        name="StatusCheck",
        expression="IIF({Amount} > 100, 'High', 'Low')",
        return_type=DataType.STRING,
        syntax=FormulaSyntax.CRYSTAL,
    )


@pytest.fixture
def sample_field():
    """Create a sample database field."""
    return Field(
        name="CustomerName",
        source="CUSTOMER_NAME",
        source_type="database",
        x=10.0,
        y=20.0,
        width=150.0,
        height=14.0,
        font=FontSpec(name="Arial", size=10, bold=False, italic=False),
        format=FormatSpec(horizontal_alignment="left", vertical_alignment="top"),
    )


@pytest.fixture
def sample_formula_field():
    """Create a sample formula field."""
    return Field(
        name="CalculatedField",
        source="@MyFormula",
        source_type="formula",
        x=10.0,
        y=20.0,
        width=100.0,
        height=14.0,
        font=FontSpec(name="Arial", size=10),
        format=FormatSpec(horizontal_alignment="right"),
    )


@pytest.fixture
def sample_section():
    """Create a sample detail section."""
    return Section(
        name="Detail",
        section_type=SectionType.DETAIL,
        height=20.0,
        fields=[
            Field(
                name="Field1",
                source="COLUMN1",
                source_type="database",
                x=10.0,
                y=5.0,
                width=100.0,
                height=14.0,
            ),
            Field(
                name="Field2",
                source="COLUMN2",
                source_type="database",
                x=120.0,
                y=5.0,
                width=100.0,
                height=14.0,
            ),
        ],
    )


@pytest.fixture
def sample_group():
    """Create a sample group."""
    return Group(name="CustomerGroup", field_name="Customer", sort_direction="ascending")


@pytest.fixture
def sample_query():
    """Create a sample query."""
    return Query(
        name="MainQuery",
        sql="SELECT * FROM CUSTOMERS",
        tables=["CUSTOMERS"],
        columns=[
            QueryColumn(name="CUSTOMER_ID", data_type=DataType.NUMBER, table_name="CUSTOMERS"),
            QueryColumn(
                name="CUSTOMER_NAME", data_type=DataType.STRING, table_name="CUSTOMERS", length=100
            ),
            QueryColumn(name="ORDER_DATE", data_type=DataType.DATE, table_name="CUSTOMERS"),
            QueryColumn(
                name="AMOUNT",
                data_type=DataType.CURRENCY,
                table_name="CUSTOMERS",
                precision=15,
                scale=2,
            ),
        ],
    )


@pytest.fixture
def sample_page_header_section():
    """Create a sample page header section."""
    return Section(
        name="PageHeader",
        section_type=SectionType.PAGE_HEADER,
        height=30.0,
        fields=[
            Field(
                name="Title",
                source="'Report Title'",
                source_type="database",
                x=200.0,
                y=10.0,
                width=200.0,
                height=16.0,
                font=FontSpec(name="Arial", size=14, bold=True),
            )
        ],
    )


@pytest.fixture
def sample_page_footer_section():
    """Create a sample page footer section."""
    return Section(
        name="PageFooter",
        section_type=SectionType.PAGE_FOOTER,
        height=25.0,
        fields=[
            Field(
                name="PageNumber",
                source="PageNumber",
                source_type="special",
                x=280.0,
                y=5.0,
                width=50.0,
                height=14.0,
            )
        ],
    )


@pytest.fixture
def sample_group_header_section():
    """Create a sample group header section."""
    return Section(
        name="GroupHeader1",
        section_type=SectionType.GROUP_HEADER,
        group_number=1,
        height=25.0,
        fields=[
            Field(
                name="GroupField",
                source="CUSTOMER",
                source_type="database",
                x=10.0,
                y=5.0,
                width=150.0,
                height=14.0,
                font=FontSpec(bold=True),
            )
        ],
    )


@pytest.fixture
def sample_group_footer_section():
    """Create a sample group footer section."""
    return Section(
        name="GroupFooter1",
        section_type=SectionType.GROUP_FOOTER,
        group_number=1,
        height=25.0,
        fields=[
            Field(
                name="GroupTotal",
                source="@GroupTotal",
                source_type="formula",
                x=200.0,
                y=5.0,
                width=100.0,
                height=14.0,
            )
        ],
    )


# Font fixtures
@pytest.fixture
def bold_font():
    """Create a bold font specification."""
    return FontSpec(name="Arial", size=12, bold=True, italic=False)


@pytest.fixture
def italic_font():
    """Create an italic font specification."""
    return FontSpec(name="Arial", size=10, bold=False, italic=True)


@pytest.fixture
def bold_italic_font():
    """Create a bold italic font specification."""
    return FontSpec(name="Arial", size=11, bold=True, italic=True)


# Format fixtures
@pytest.fixture
def left_aligned_format():
    """Create a left-aligned format specification."""
    return FormatSpec(horizontal_alignment="left", vertical_alignment="top")


@pytest.fixture
def center_aligned_format():
    """Create a center-aligned format specification."""
    return FormatSpec(horizontal_alignment="center", vertical_alignment="center")


@pytest.fixture
def right_aligned_format():
    """Create a right-aligned format specification."""
    return FormatSpec(horizontal_alignment="right", vertical_alignment="top")


@pytest.fixture
def currency_format():
    """Create a currency format specification."""
    return FormatSpec(
        format_string="$#,##0.00", horizontal_alignment="right", suppress_if_zero=False
    )


@pytest.fixture
def date_format():
    """Create a date format specification."""
    return FormatSpec(format_string="MM/dd/yyyy", horizontal_alignment="left")


# Collection fixtures
@pytest.fixture
def sample_formula_list():
    """Create a list of sample formulas."""
    return [
        Formula(name="Formula1", expression="{Field1} & {Field2}", return_type=DataType.STRING),
        Formula(name="Formula2", expression="{Amount} * 1.1", return_type=DataType.NUMBER),
        Formula(
            name="Formula3",
            expression="IIF({Status} = 'A', 'Active', 'Inactive')",
            return_type=DataType.STRING,
        ),
    ]


@pytest.fixture
def sample_section_list(sample_page_header_section, sample_section, sample_page_footer_section):
    """Create a list of sample sections."""
    return [
        sample_page_header_section,
        sample_section,
        sample_page_footer_section,
    ]


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Tests that take significant time")
    config.addinivalue_line("markers", "formula: Formula translation tests")
    config.addinivalue_line("markers", "type: Type mapping tests")
    config.addinivalue_line("markers", "layout: Layout mapping tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test file name
        if "test_formula_translator" in item.nodeid:
            item.add_marker(pytest.mark.formula)
            item.add_marker(pytest.mark.unit)
        elif "test_type_mapper" in item.nodeid:
            item.add_marker(pytest.mark.type)
            item.add_marker(pytest.mark.unit)
        elif "test_layout_mapper" in item.nodeid:
            item.add_marker(pytest.mark.layout)
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
