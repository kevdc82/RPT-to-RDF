"""Generation module - Generates Oracle Reports XML and converts to RDF."""

from .oracle_xml_generator import OracleXMLGenerator
from .rdf_converter import RDFConverter, ConversionResult

__all__ = ["OracleXMLGenerator", "RDFConverter", "ConversionResult"]
