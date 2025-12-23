"""
Unit tests for Type Mapper.

Tests the conversion of Crystal Reports data types to Oracle data types.
"""

import pytest

from src.parsing.report_model import DataType
from src.transformation.type_mapper import OracleType, TypeMapper


class TestOracleType:
    """Test suite for OracleType dataclass."""

    def test_simple_type_str(self):
        """Test string representation of simple type."""
        oracle_type = OracleType(name="VARCHAR2", length=100)
        assert str(oracle_type) == "VARCHAR2(100)"

    def test_type_with_precision_only(self):
        """Test type with precision only."""
        oracle_type = OracleType(name="NUMBER", precision=10)
        assert str(oracle_type) == "NUMBER(10)"

    def test_type_with_precision_and_scale(self):
        """Test type with precision and scale."""
        oracle_type = OracleType(name="NUMBER", precision=15, scale=2)
        assert str(oracle_type) == "NUMBER(15,2)"

    def test_type_without_parameters(self):
        """Test type without length, precision, or scale."""
        oracle_type = OracleType(name="DATE")
        assert str(oracle_type) == "DATE"

    def test_type_length_overrides_precision(self):
        """Test that length takes precedence."""
        oracle_type = OracleType(name="VARCHAR2", length=4000, precision=10)
        assert str(oracle_type) == "VARCHAR2(4000)"


class TestTypeMapper:
    """Test suite for TypeMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TypeMapper()

    # Basic type mapping tests
    def test_string_type_mapping(self):
        """Test STRING to VARCHAR2 mapping."""
        oracle_type = self.mapper.map_type(DataType.STRING)
        assert oracle_type.name == "VARCHAR2"
        assert oracle_type.length == 4000

    def test_number_type_mapping(self):
        """Test NUMBER type mapping."""
        oracle_type = self.mapper.map_type(DataType.NUMBER)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.length is None
        assert oracle_type.precision is None

    def test_currency_type_mapping(self):
        """Test CURRENCY type mapping."""
        oracle_type = self.mapper.map_type(DataType.CURRENCY)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.precision == 15
        assert oracle_type.scale == 2

    def test_date_type_mapping(self):
        """Test DATE type mapping."""
        oracle_type = self.mapper.map_type(DataType.DATE)
        assert oracle_type.name == "DATE"

    def test_time_type_mapping(self):
        """Test TIME type mapping (Oracle uses DATE)."""
        oracle_type = self.mapper.map_type(DataType.TIME)
        assert oracle_type.name == "DATE"

    def test_datetime_type_mapping(self):
        """Test DATETIME to TIMESTAMP mapping."""
        oracle_type = self.mapper.map_type(DataType.DATETIME)
        assert oracle_type.name == "TIMESTAMP"

    def test_boolean_type_mapping(self):
        """Test BOOLEAN to VARCHAR2(1) mapping."""
        oracle_type = self.mapper.map_type(DataType.BOOLEAN)
        assert oracle_type.name == "VARCHAR2"
        assert oracle_type.length == 1

    def test_memo_type_mapping(self):
        """Test MEMO to CLOB mapping."""
        oracle_type = self.mapper.map_type(DataType.MEMO)
        assert oracle_type.name == "CLOB"

    def test_blob_type_mapping(self):
        """Test BLOB type mapping."""
        oracle_type = self.mapper.map_type(DataType.BLOB)
        assert oracle_type.name == "BLOB"

    def test_unknown_type_mapping(self):
        """Test UNKNOWN type defaults to VARCHAR2."""
        oracle_type = self.mapper.map_type(DataType.UNKNOWN)
        assert oracle_type.name == "VARCHAR2"
        assert oracle_type.length == 4000

    # Type mapping with overrides
    def test_string_with_custom_length(self):
        """Test STRING type with custom length."""
        oracle_type = self.mapper.map_type(DataType.STRING, length=255)
        assert oracle_type.name == "VARCHAR2"
        assert oracle_type.length == 255

    def test_number_with_precision(self):
        """Test NUMBER type with precision."""
        oracle_type = self.mapper.map_type(DataType.NUMBER, precision=10)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.precision == 10

    def test_number_with_precision_and_scale(self):
        """Test NUMBER type with precision and scale."""
        oracle_type = self.mapper.map_type(DataType.NUMBER, precision=10, scale=2)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.precision == 10
        assert oracle_type.scale == 2

    def test_currency_with_custom_precision(self):
        """Test CURRENCY type with custom precision."""
        oracle_type = self.mapper.map_type(DataType.CURRENCY, precision=20, scale=4)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.precision == 20
        assert oracle_type.scale == 4

    # String type mapping tests
    def test_map_type_string(self):
        """Test map_type_string returns formatted string."""
        type_str = self.mapper.map_type_string(DataType.STRING)
        assert type_str == "VARCHAR2(4000)"

    def test_map_type_string_with_length(self):
        """Test map_type_string with custom length."""
        type_str = self.mapper.map_type_string(DataType.STRING, length=100)
        assert type_str == "VARCHAR2(100)"

    def test_map_type_string_number_with_precision(self):
        """Test map_type_string for NUMBER with precision."""
        type_str = self.mapper.map_type_string(DataType.NUMBER, precision=10, scale=2)
        assert type_str == "NUMBER(10,2)"

    def test_map_type_string_date(self):
        """Test map_type_string for DATE."""
        type_str = self.mapper.map_type_string(DataType.DATE)
        assert type_str == "DATE"

    # Format string mapping tests
    def test_format_number_with_commas(self):
        """Test number format with comma separator."""
        oracle_format = self.mapper.map_format_string("#,##0")
        assert oracle_format == "999,999,999,990"

    def test_format_number_with_decimals(self):
        """Test number format with decimal places."""
        oracle_format = self.mapper.map_format_string("#,##0.00")
        assert oracle_format == "999,999,999,990.00"

    def test_format_currency_simple(self):
        """Test simple currency format."""
        oracle_format = self.mapper.map_format_string("$#,##0")
        assert oracle_format == "$999,999,999,990"

    def test_format_currency_with_decimals(self):
        """Test currency format with decimals."""
        oracle_format = self.mapper.map_format_string("$#,##0.00")
        assert oracle_format == "$999,999,999,990.00"

    def test_format_date_mmddyyyy(self):
        """Test MM/dd/yyyy date format."""
        oracle_format = self.mapper.map_format_string("MM/dd/yyyy")
        assert oracle_format == "MM/DD/YYYY"

    def test_format_date_ddmmyyyy(self):
        """Test dd/MM/yyyy date format."""
        oracle_format = self.mapper.map_format_string("dd/MM/yyyy")
        assert oracle_format == "DD/MM/YYYY"

    def test_format_date_iso(self):
        """Test ISO date format."""
        oracle_format = self.mapper.map_format_string("yyyy-MM-dd")
        assert oracle_format == "YYYY-MM-DD"

    def test_format_date_long_month(self):
        """Test date format with full month name."""
        oracle_format = self.mapper.map_format_string("MMMM d, yyyy")
        assert oracle_format == "MONTH DD, YYYY"

    def test_format_date_short_month(self):
        """Test date format with abbreviated month."""
        oracle_format = self.mapper.map_format_string("MMM d, yyyy")
        assert oracle_format == "MON DD, YYYY"

    def test_format_time_12hour(self):
        """Test 12-hour time format."""
        oracle_format = self.mapper.map_format_string("h:mm:ss tt")
        assert oracle_format == "HH:MI:SS AM"

    def test_format_time_24hour(self):
        """Test 24-hour time format."""
        oracle_format = self.mapper.map_format_string("HH:mm:ss")
        assert oracle_format == "HH24:MI:SS"

    def test_format_datetime_combined(self):
        """Test combined date and time format."""
        oracle_format = self.mapper.map_format_string("MM/dd/yyyy h:mm:ss tt")
        assert oracle_format == "MM/DD/YYYY HH:MI:SS AM"

    def test_format_empty_string(self):
        """Test empty format string returns None."""
        oracle_format = self.mapper.map_format_string("")
        assert oracle_format is None

    def test_format_none(self):
        """Test None format string returns None."""
        oracle_format = self.mapper.map_format_string(None)
        assert oracle_format is None

    def test_format_unknown_pattern(self):
        """Test unknown format pattern."""
        oracle_format = self.mapper.map_format_string("custom_format")
        # Should return None or attempt conversion
        assert oracle_format is None or isinstance(oracle_format, str)

    # Default value tests
    def test_default_value_none(self):
        """Test default value for None."""
        result = self.mapper.get_default_value(DataType.STRING, None)
        assert result == "NULL"

    def test_default_value_string(self):
        """Test default value for string."""
        result = self.mapper.get_default_value(DataType.STRING, "test")
        assert result == "'test'"

    def test_default_value_string_with_quotes(self):
        """Test default value for string with single quotes."""
        result = self.mapper.get_default_value(DataType.STRING, "test'value")
        assert result == "'test''value'"  # Escaped single quote

    def test_default_value_number(self):
        """Test default value for number."""
        result = self.mapper.get_default_value(DataType.NUMBER, "123")
        assert result == "123"

    def test_default_value_currency(self):
        """Test default value for currency."""
        result = self.mapper.get_default_value(DataType.CURRENCY, "100.50")
        assert result == "100.50"

    def test_default_value_boolean_true(self):
        """Test default value for boolean true."""
        result = self.mapper.get_default_value(DataType.BOOLEAN, "true")
        assert result == "'Y'"

    def test_default_value_boolean_false(self):
        """Test default value for boolean false."""
        result = self.mapper.get_default_value(DataType.BOOLEAN, "false")
        assert result == "'N'"

    def test_default_value_boolean_yes(self):
        """Test default value for boolean 'yes'."""
        result = self.mapper.get_default_value(DataType.BOOLEAN, "yes")
        assert result == "'Y'"

    def test_default_value_boolean_one(self):
        """Test default value for boolean '1'."""
        result = self.mapper.get_default_value(DataType.BOOLEAN, "1")
        assert result == "'Y'"

    def test_default_value_date(self):
        """Test default value for date."""
        result = self.mapper.get_default_value(DataType.DATE, "2024-01-15")
        assert "TO_DATE" in result
        assert "2024-01-15" in result

    def test_default_value_datetime(self):
        """Test default value for datetime."""
        result = self.mapper.get_default_value(DataType.DATETIME, "2024-01-15")
        assert "TO_DATE" in result

    def test_default_value_time(self):
        """Test default value for time."""
        result = self.mapper.get_default_value(DataType.TIME, "14:30:00")
        assert "TO_DATE" in result
        assert "14:30:00" in result

    def test_default_value_memo(self):
        """Test default value for memo."""
        result = self.mapper.get_default_value(DataType.MEMO, "long text")
        assert result == "'long text'"

    # Conversion function tests
    def test_requires_conversion_datetime(self):
        """Test conversion function for DATETIME."""
        func = self.mapper.requires_conversion_function(DataType.DATETIME)
        assert func == "TO_TIMESTAMP"

    def test_requires_conversion_date(self):
        """Test conversion function for DATE."""
        func = self.mapper.requires_conversion_function(DataType.DATE)
        assert func == "TO_DATE"

    def test_requires_conversion_time(self):
        """Test conversion function for TIME."""
        func = self.mapper.requires_conversion_function(DataType.TIME)
        assert func == "TO_DATE"

    def test_requires_conversion_string(self):
        """Test no conversion function for STRING."""
        func = self.mapper.requires_conversion_function(DataType.STRING)
        assert func is None

    def test_requires_conversion_number(self):
        """Test no conversion function for NUMBER."""
        func = self.mapper.requires_conversion_function(DataType.NUMBER)
        assert func is None

    # PL/SQL type tests
    def test_plsql_type_string(self):
        """Test PL/SQL type for STRING."""
        plsql_type = self.mapper.get_plsql_type(DataType.STRING)
        assert plsql_type == "VARCHAR2(4000)"

    def test_plsql_type_number(self):
        """Test PL/SQL type for NUMBER."""
        plsql_type = self.mapper.get_plsql_type(DataType.NUMBER)
        assert plsql_type == "NUMBER"

    def test_plsql_type_currency(self):
        """Test PL/SQL type for CURRENCY."""
        plsql_type = self.mapper.get_plsql_type(DataType.CURRENCY)
        assert plsql_type == "NUMBER"

    def test_plsql_type_date(self):
        """Test PL/SQL type for DATE."""
        plsql_type = self.mapper.get_plsql_type(DataType.DATE)
        assert plsql_type == "DATE"

    def test_plsql_type_datetime(self):
        """Test PL/SQL type for DATETIME."""
        plsql_type = self.mapper.get_plsql_type(DataType.DATETIME)
        assert plsql_type == "TIMESTAMP"

    def test_plsql_type_boolean(self):
        """Test PL/SQL type for BOOLEAN."""
        plsql_type = self.mapper.get_plsql_type(DataType.BOOLEAN)
        assert plsql_type == "BOOLEAN"  # PL/SQL supports BOOLEAN

    def test_plsql_type_memo(self):
        """Test PL/SQL type for MEMO."""
        plsql_type = self.mapper.get_plsql_type(DataType.MEMO)
        assert plsql_type == "CLOB"

    def test_plsql_type_blob(self):
        """Test PL/SQL type for BLOB."""
        plsql_type = self.mapper.get_plsql_type(DataType.BLOB)
        assert plsql_type == "BLOB"

    def test_plsql_type_unknown(self):
        """Test PL/SQL type for UNKNOWN."""
        plsql_type = self.mapper.get_plsql_type(DataType.UNKNOWN)
        assert plsql_type == "VARCHAR2(4000)"


class TestTypeMapperCustomMappings:
    """Test TypeMapper with custom mappings."""

    def test_custom_string_length(self):
        """Test custom mapping for STRING with different default length."""
        custom_mappings = {DataType.STRING: OracleType("VARCHAR2", length=2000)}
        mapper = TypeMapper(custom_mappings=custom_mappings)
        oracle_type = mapper.map_type(DataType.STRING)
        assert oracle_type.length == 2000

    def test_custom_currency_precision(self):
        """Test custom mapping for CURRENCY with different precision."""
        custom_mappings = {DataType.CURRENCY: OracleType("NUMBER", precision=20, scale=4)}
        mapper = TypeMapper(custom_mappings=custom_mappings)
        oracle_type = mapper.map_type(DataType.CURRENCY)
        assert oracle_type.precision == 20
        assert oracle_type.scale == 4

    def test_custom_boolean_mapping(self):
        """Test custom mapping for BOOLEAN to NUMBER."""
        custom_mappings = {DataType.BOOLEAN: OracleType("NUMBER", precision=1)}
        mapper = TypeMapper(custom_mappings=custom_mappings)
        oracle_type = mapper.map_type(DataType.BOOLEAN)
        assert oracle_type.name == "NUMBER"
        assert oracle_type.precision == 1

    def test_partial_custom_mappings(self):
        """Test that custom mappings only override specified types."""
        custom_mappings = {DataType.STRING: OracleType("VARCHAR2", length=1000)}
        mapper = TypeMapper(custom_mappings=custom_mappings)

        # Custom mapping applied
        string_type = mapper.map_type(DataType.STRING)
        assert string_type.length == 1000

        # Default mapping still used for others
        number_type = mapper.map_type(DataType.NUMBER)
        assert number_type.name == "NUMBER"


class TestTypeMapperEdgeCases:
    """Test edge cases for TypeMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TypeMapper()

    def test_zero_length(self):
        """Test mapping with zero length."""
        oracle_type = self.mapper.map_type(DataType.STRING, length=0)
        assert oracle_type.length == 0
        assert str(oracle_type) == "VARCHAR2(0)"

    def test_very_large_length(self):
        """Test mapping with very large length."""
        oracle_type = self.mapper.map_type(DataType.STRING, length=32767)
        assert oracle_type.length == 32767

    def test_negative_precision(self):
        """Test mapping with negative precision (edge case)."""
        oracle_type = self.mapper.map_type(DataType.NUMBER, precision=-1)
        assert oracle_type.precision == -1

    def test_zero_scale(self):
        """Test mapping with zero scale."""
        oracle_type = self.mapper.map_type(DataType.NUMBER, precision=10, scale=0)
        assert oracle_type.scale == 0
        assert str(oracle_type) == "NUMBER(10,0)"

    def test_scale_without_precision(self):
        """Test mapping with scale but no precision."""
        oracle_type = self.mapper.map_type(DataType.NUMBER, scale=2)
        # Scale should be set even without precision
        assert oracle_type.scale == 2

    def test_format_with_special_characters(self):
        """Test format string with special characters."""
        # Format with parentheses for negative numbers
        oracle_format = self.mapper.map_format_string("#,##0.00;(#,##0.00)")
        assert oracle_format == "999,999,999,990.00PR"

    def test_format_percentage(self):
        """Test percentage format."""
        oracle_format = self.mapper.map_format_string("0%")
        assert oracle_format == "990%"

    def test_format_percentage_with_decimals(self):
        """Test percentage format with decimals."""
        oracle_format = self.mapper.map_format_string("0.00%")
        assert oracle_format == "990.00%"

    def test_default_value_empty_string(self):
        """Test default value for empty string."""
        result = self.mapper.get_default_value(DataType.STRING, "")
        assert result == "''"

    def test_default_value_zero_number(self):
        """Test default value for zero number."""
        result = self.mapper.get_default_value(DataType.NUMBER, "0")
        assert result == "0"

    def test_default_value_negative_number(self):
        """Test default value for negative number."""
        result = self.mapper.get_default_value(DataType.NUMBER, "-123.45")
        assert result == "-123.45"


class TestFormatMapping:
    """Additional tests for format string mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TypeMapper()

    def test_date_component_yyyy(self):
        """Test yyyy date component conversion."""
        result = self.mapper.map_format_string("yyyy")
        assert "YYYY" in result

    def test_date_component_yy(self):
        """Test yy date component conversion."""
        result = self.mapper.map_format_string("yy")
        assert "YY" in result

    def test_date_component_mm_month(self):
        """Test MM month component conversion."""
        result = self.mapper.map_format_string("MM")
        assert "MM" in result

    def test_date_component_dd(self):
        """Test dd day component conversion."""
        result = self.mapper.map_format_string("dd")
        assert "DD" in result

    def test_time_component_hh24(self):
        """Test HH (24-hour) component conversion."""
        result = self.mapper.map_format_string("HH:mm:ss")
        assert "HH24" in result
        assert "MI" in result
        assert "SS" in result

    def test_time_component_hh12(self):
        """Test hh (12-hour) component conversion."""
        result = self.mapper.map_format_string("h:mm tt")
        assert "HH" in result or "AM" in result
        assert "MI" in result

    def test_complex_format_pattern(self):
        """Test complex format pattern with multiple components."""
        result = self.mapper.map_format_string("yyyy-MM-dd HH:mm:ss")
        assert "YYYY" in result
        assert "MM" in result
        assert "DD" in result
        assert "HH24" in result
        assert "MI" in result
        assert "SS" in result
