"""
Integration tests for RPT to RDF Converter.

Tests the complete transformation pipeline from Crystal Reports to Oracle Reports.
"""

import pytest
from src.transformation.formula_translator import FormulaTranslator
from src.transformation.type_mapper import TypeMapper
from src.transformation.layout_mapper import LayoutMapper
from src.parsing.report_model import (
    ReportModel,
    Formula,
    Section,
    Field,
    Group,
    Query,
    QueryColumn,
    SectionType,
    DataType,
    FontSpec,
    FormatSpec,
)


class TestEndToEndTransformation:
    """Test complete transformation pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formula_translator = FormulaTranslator()
        self.type_mapper = TypeMapper()
        self.layout_mapper = LayoutMapper()

    def test_simple_report_transformation(self):
        """Test transformation of a simple report with basic fields."""
        # Create a simple Crystal report structure
        query = Query(
            name="MainQuery",
            sql="SELECT * FROM CUSTOMERS",
            columns=[
                QueryColumn(name="CUSTOMER_ID", data_type=DataType.NUMBER),
                QueryColumn(name="CUSTOMER_NAME", data_type=DataType.STRING),
                QueryColumn(name="AMOUNT", data_type=DataType.CURRENCY),
            ]
        )

        detail_section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=[
                Field(
                    name="CustomerName",
                    source="CUSTOMER_NAME",
                    source_type="database",
                    x=10.0,
                    y=5.0,
                    width=150.0,
                    height=14.0
                ),
                Field(
                    name="Amount",
                    source="AMOUNT",
                    source_type="database",
                    x=170.0,
                    y=5.0,
                    width=100.0,
                    height=14.0,
                    format=FormatSpec(format_string="$#,##0.00")
                ),
            ]
        )

        # Map types
        for column in query.columns:
            oracle_type = self.type_mapper.map_type(column.data_type)
            assert oracle_type is not None

        # Map layout
        layout = self.layout_mapper.map_layout([detail_section], [], 612.0, 792.0)

        assert layout.body_frame is not None
        assert len(layout.all_frames) > 0

    def test_report_with_formulas(self):
        """Test transformation of report with formulas."""
        # Create formulas
        formulas = [
            Formula(
                name="FullName",
                expression="{FirstName} & ' ' & {LastName}",
                return_type=DataType.STRING
            ),
            Formula(
                name="DiscountedAmount",
                expression="IIF({Amount} > 1000, {Amount} * 0.9, {Amount})",
                return_type=DataType.NUMBER
            ),
            Formula(
                name="Status",
                expression="IIF({Active}, 'Active', 'Inactive')",
                return_type=DataType.STRING
            ),
        ]

        # Translate formulas
        translated = self.formula_translator.batch_translate(formulas)

        assert len(translated) == 3
        assert all(t.success for t in translated)

        # Check specific translations
        full_name = next(t for t in translated if t.original_name == "FullName")
        assert "||" in full_name.plsql_code
        assert "FIRSTNAME" in full_name.referenced_columns
        assert "LASTNAME" in full_name.referenced_columns

        discounted = next(t for t in translated if t.original_name == "DiscountedAmount")
        assert "CASE WHEN" in discounted.plsql_code

    def test_report_with_groups(self):
        """Test transformation of report with grouping."""
        # Create groups
        groups = [
            Group(name="Region", field_name="Region"),
            Group(name="Customer", field_name="Customer"),
        ]

        # Create sections for grouped report
        sections = [
            Section(
                name="GroupHeader1",
                section_type=SectionType.GROUP_HEADER,
                group_number=1,
                height=25.0,
                fields=[
                    Field(name="RegionLabel", source="Region", x=10.0, y=5.0)
                ]
            ),
            Section(
                name="GroupHeader2",
                section_type=SectionType.GROUP_HEADER,
                group_number=2,
                height=20.0,
                fields=[
                    Field(name="CustomerLabel", source="Customer", x=20.0, y=5.0)
                ]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=15.0,
                fields=[
                    Field(name="OrderID", source="OrderID", x=30.0, y=5.0)
                ]
            ),
            Section(
                name="GroupFooter2",
                section_type=SectionType.GROUP_FOOTER,
                group_number=2,
                height=20.0,
                fields=[]
            ),
            Section(
                name="GroupFooter1",
                section_type=SectionType.GROUP_FOOTER,
                group_number=1,
                height=25.0,
                fields=[]
            ),
        ]

        # Map layout
        layout = self.layout_mapper.map_layout(sections, groups, 612.0, 792.0)

        assert layout.body_frame is not None
        # Should have nested repeating frames for groups
        assert len(layout.body_frame.children) > 0

    def test_report_with_all_sections(self):
        """Test transformation of report with all section types."""
        sections = [
            Section(
                name="ReportHeader",
                section_type=SectionType.REPORT_HEADER,
                height=50.0,
                fields=[
                    Field(name="Title", source="'Sales Report'", x=200.0, y=10.0)
                ]
            ),
            Section(
                name="PageHeader",
                section_type=SectionType.PAGE_HEADER,
                height=30.0,
                fields=[
                    Field(name="ColumnHeader", source="'Customer'", x=10.0, y=5.0)
                ]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[
                    Field(name="CustomerName", source="CUSTOMER_NAME", x=10.0, y=5.0)
                ]
            ),
            Section(
                name="PageFooter",
                section_type=SectionType.PAGE_FOOTER,
                height=25.0,
                fields=[
                    Field(name="PageNumber", source="PageNumber", x=280.0, y=5.0)
                ]
            ),
            Section(
                name="ReportFooter",
                section_type=SectionType.REPORT_FOOTER,
                height=40.0,
                fields=[
                    Field(name="Summary", source="'End of Report'", x=200.0, y=10.0)
                ]
            ),
        ]

        layout = self.layout_mapper.map_layout(sections, [], 612.0, 792.0)

        assert layout.margin_frame is not None
        assert layout.header_frame is not None
        assert layout.body_frame is not None
        assert layout.trailer_frame is not None

    def test_complex_formula_with_type_mapping(self):
        """Test complex formula translation with type mapping."""
        formula = Formula(
            name="ComplexCalculation",
            expression="""
                IIF(
                    {OrderDate} > CurrentDate - 30,
                    Round({Amount} * 1.05, 2),
                    {Amount}
                )
            """,
            return_type=DataType.CURRENCY
        )

        # Translate formula
        translated = self.formula_translator.translate(formula)

        assert translated.success
        assert "CASE WHEN" in translated.plsql_code
        assert "ROUND" in translated.plsql_code.upper()

        # Check return type mapping
        return_type = self.type_mapper.map_type(formula.return_type)
        assert return_type.name == "NUMBER"
        assert return_type.precision == 15
        assert return_type.scale == 2

    def test_field_formatting_integration(self):
        """Test field formatting with type mapper."""
        field = Field(
            name="OrderDate",
            source="ORDER_DATE",
            source_type="database",
            format=FormatSpec(format_string="MM/dd/yyyy")
        )

        # Map field to Oracle
        oracle_field = self.layout_mapper._map_field(field)

        # Map format string
        oracle_format = self.type_mapper.map_format_string(field.format.format_string)

        assert oracle_format == "MM/DD/YYYY"
        assert oracle_field.format_mask == "MM/dd/yyyy"

    def test_multiple_data_types_in_detail_section(self):
        """Test detail section with multiple data types."""
        fields = [
            Field(
                name="OrderID",
                source="ORDER_ID",
                source_type="database",
                x=10.0,
                y=5.0
            ),
            Field(
                name="OrderDate",
                source="ORDER_DATE",
                source_type="database",
                x=80.0,
                y=5.0,
                format=FormatSpec(format_string="MM/dd/yyyy")
            ),
            Field(
                name="Amount",
                source="AMOUNT",
                source_type="database",
                x=160.0,
                y=5.0,
                format=FormatSpec(format_string="$#,##0.00")
            ),
            Field(
                name="Active",
                source="ACTIVE",
                source_type="database",
                x=260.0,
                y=5.0
            ),
        ]

        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=fields
        )

        frame = self.layout_mapper._map_section(section, 600.0, [])

        assert len(frame.fields) == 4
        assert all(f.name.startswith("F_") for f in frame.fields)


class TestFormulaAndTypeIntegration:
    """Test integration between formula translator and type mapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formula_translator = FormulaTranslator()
        self.type_mapper = TypeMapper()

    def test_string_formula_with_type(self):
        """Test string formula with appropriate type mapping."""
        formula = Formula(
            name="CombinedName",
            expression="Upper({FirstName}) & ' ' & Upper({LastName})",
            return_type=DataType.STRING
        )

        translated = self.formula_translator.translate(formula)
        oracle_type = self.type_mapper.map_type(formula.return_type)

        assert translated.return_type == "VARCHAR2"
        assert oracle_type.name == "VARCHAR2"

    def test_numeric_formula_with_precision(self):
        """Test numeric formula with precision handling."""
        formula = Formula(
            name="Calculation",
            expression="Round({Price} * {Quantity}, 2)",
            return_type=DataType.NUMBER
        )

        translated = self.formula_translator.translate(formula)

        # Check that ROUND is properly translated
        assert "ROUND" in translated.plsql_code.upper()

        # Map with custom precision
        oracle_type = self.type_mapper.map_type(
            formula.return_type,
            precision=10,
            scale=2
        )

        assert str(oracle_type) == "NUMBER(10,2)"

    def test_date_formula_with_formatting(self):
        """Test date formula with format conversion."""
        formula = Formula(
            name="FormattedDate",
            expression="Year({OrderDate}) & '-' & Month({OrderDate})",
            return_type=DataType.STRING
        )

        translated = self.formula_translator.translate(formula)

        assert "EXTRACT(YEAR" in translated.plsql_code.upper()
        assert "EXTRACT(MONTH" in translated.plsql_code.upper()


class TestLayoutAndFormulaIntegration:
    """Test integration between layout mapper and formula translator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formula_translator = FormulaTranslator()
        self.layout_mapper = LayoutMapper()

    def test_formula_field_in_section(self):
        """Test section containing formula field."""
        # Create formula
        formula = Formula(
            name="CalculatedField",
            expression="{Amount} * 1.1",
            return_type=DataType.NUMBER
        )

        # Translate formula
        translated = self.formula_translator.translate(formula)

        # Create field referencing formula
        field = Field(
            name="CalcField",
            source="@CalculatedField",
            source_type="formula",
            x=10.0,
            y=5.0
        )

        # Map field
        oracle_field = self.layout_mapper._map_field(field)

        assert oracle_field.source_type == "formula"
        assert "@" not in oracle_field.source

    def test_multiple_formula_fields(self):
        """Test section with multiple formula fields."""
        formulas = [
            Formula(name="Total", expression="{Qty} * {Price}", return_type=DataType.NUMBER),
            Formula(name="Tax", expression="{Total} * 0.08", return_type=DataType.NUMBER),
            Formula(name="GrandTotal", expression="{Total} + {Tax}", return_type=DataType.NUMBER),
        ]

        # Translate all formulas
        translated = self.formula_translator.batch_translate(formulas)

        # Create fields
        fields = [
            Field(name="TotalField", source="@Total", source_type="formula", x=10.0, y=5.0),
            Field(name="TaxField", source="@Tax", source_type="formula", x=120.0, y=5.0),
            Field(name="GrandTotalField", source="@GrandTotal", source_type="formula", x=230.0, y=5.0),
        ]

        section = Section(
            name="Detail",
            section_type=SectionType.DETAIL,
            height=20.0,
            fields=fields
        )

        frame = self.layout_mapper._map_section(section, 600.0, [])

        assert len(frame.fields) == 3
        assert all(f.source_type == "formula" for f in frame.fields)


class TestErrorHandlingIntegration:
    """Test error handling across transformation components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formula_translator = FormulaTranslator(on_unsupported="placeholder")
        self.type_mapper = TypeMapper()
        self.layout_mapper = LayoutMapper()

    def test_empty_formula_handling(self):
        """Test handling of empty formula."""
        formula = Formula(
            name="EmptyFormula",
            expression="",
            return_type=DataType.STRING
        )

        translated = self.formula_translator.translate(formula)

        assert translated.success
        assert len(translated.warnings) > 0
        assert "NULL" in translated.plsql_code.upper()

    def test_unknown_type_mapping(self):
        """Test handling of unknown data type."""
        oracle_type = self.type_mapper.map_type(DataType.UNKNOWN)

        # Should default to VARCHAR2
        assert oracle_type.name == "VARCHAR2"
        assert oracle_type.length == 4000

    def test_section_with_no_fields(self):
        """Test section with no fields.

        Note: Height is converted from twips to points (1 twip = 0.05 points).
        20 twips = 1.0 points.
        """
        section = Section(
            name="EmptyDetail",
            section_type=SectionType.DETAIL,
            height=20.0,  # twips
            fields=[]
        )

        frame = self.layout_mapper._map_section(section, 600.0, [])

        assert len(frame.fields) == 0
        # Height is converted from twips to points
        assert frame.height == 1.0  # 20 twips = 1.0 points


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formula_translator = FormulaTranslator()
        self.type_mapper = TypeMapper()
        self.layout_mapper = LayoutMapper()

    def test_invoice_report_structure(self):
        """Test transformation of invoice-like report structure."""
        # Create formulas for calculations
        formulas = [
            Formula(
                name="LineTotal",
                expression="{Quantity} * {UnitPrice}",
                return_type=DataType.CURRENCY
            ),
            Formula(
                name="Tax",
                expression="{LineTotal} * {TaxRate}",
                return_type=DataType.CURRENCY
            ),
            Formula(
                name="GrandTotal",
                expression="{LineTotal} + {Tax}",
                return_type=DataType.CURRENCY
            ),
        ]

        # Translate formulas
        translated_formulas = self.formula_translator.batch_translate(formulas)
        assert all(f.success for f in translated_formulas)

        # Create sections
        sections = [
            Section(
                name="ReportHeader",
                section_type=SectionType.REPORT_HEADER,
                height=60.0,
                fields=[
                    Field(name="InvoiceTitle", source="'INVOICE'", x=250.0, y=10.0)
                ]
            ),
            Section(
                name="PageHeader",
                section_type=SectionType.PAGE_HEADER,
                height=30.0,
                fields=[
                    Field(name="ItemHeader", source="'Item'", x=10.0, y=5.0),
                    Field(name="QtyHeader", source="'Qty'", x=150.0, y=5.0),
                    Field(name="PriceHeader", source="'Price'", x=200.0, y=5.0),
                    Field(name="TotalHeader", source="'Total'", x=250.0, y=5.0),
                ]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=20.0,
                fields=[
                    Field(name="ItemName", source="ITEM_NAME", x=10.0, y=5.0),
                    Field(name="Qty", source="QUANTITY", x=150.0, y=5.0),
                    Field(name="Price", source="UNIT_PRICE", x=200.0, y=5.0),
                    Field(name="Total", source="@LineTotal", source_type="formula", x=250.0, y=5.0),
                ]
            ),
            Section(
                name="ReportFooter",
                section_type=SectionType.REPORT_FOOTER,
                height=50.0,
                fields=[
                    Field(name="GrandTotalLabel", source="'Grand Total:'", x=200.0, y=10.0),
                    Field(name="GrandTotalValue", source="@GrandTotal", source_type="formula", x=270.0, y=10.0),
                ]
            ),
        ]

        # Map layout
        layout = self.layout_mapper.map_layout(sections, [], 612.0, 792.0)

        assert layout.header_frame is not None
        assert layout.body_frame is not None
        assert layout.margin_frame is not None
        assert len(layout.all_frames) >= 4

    def test_grouped_summary_report(self):
        """Test transformation of grouped summary report."""
        # Create group
        group = Group(name="Department", field_name="Department")

        # Create formulas
        formulas = [
            Formula(
                name="DeptTotal",
                expression="Sum({Amount}, {Department})",
                return_type=DataType.CURRENCY
            ),
            Formula(
                name="DeptAvg",
                expression="Avg({Amount}, {Department})",
                return_type=DataType.CURRENCY
            ),
        ]

        translated_formulas = self.formula_translator.batch_translate(formulas)

        # Create sections
        sections = [
            Section(
                name="GroupHeader",
                section_type=SectionType.GROUP_HEADER,
                group_number=1,
                height=25.0,
                fields=[
                    Field(name="DeptName", source="DEPARTMENT", x=10.0, y=5.0,
                          font=FontSpec(bold=True))
                ]
            ),
            Section(
                name="Detail",
                section_type=SectionType.DETAIL,
                height=18.0,
                fields=[
                    Field(name="Employee", source="EMPLOYEE_NAME", x=20.0, y=4.0),
                    Field(name="Salary", source="SALARY", x=200.0, y=4.0,
                          format=FormatSpec(format_string="$#,##0.00")),
                ]
            ),
            Section(
                name="GroupFooter",
                section_type=SectionType.GROUP_FOOTER,
                group_number=1,
                height=25.0,
                fields=[
                    Field(name="TotalLabel", source="'Department Total:'", x=120.0, y=5.0),
                    Field(name="TotalValue", source="@DeptTotal", source_type="formula", x=200.0, y=5.0),
                ]
            ),
        ]

        # Map layout
        layout = self.layout_mapper.map_layout(sections, [group], 612.0, 792.0)

        assert layout.body_frame is not None
        assert len(layout.body_frame.children) > 0

    def test_conditional_formatting_with_formulas(self):
        """Test fields with conditional formatting using formulas."""
        # Suppression formula
        suppress_formula = Formula(
            name="SuppressZero",
            expression="{Amount} = 0",
            return_type=DataType.BOOLEAN
        )

        translated = self.formula_translator.translate(suppress_formula)

        field = Field(
            name="ConditionalAmount",
            source="AMOUNT",
            x=100.0,
            y=5.0,
            suppress_condition="@SuppressZero"
        )

        oracle_field = self.layout_mapper._map_field(field)

        # Field with suppress condition should be marked
        assert oracle_field.visible is False
