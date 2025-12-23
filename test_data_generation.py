#!/usr/bin/env python3
"""Test script to verify data section generation."""

from pathlib import Path
from src.parsing.crystal_parser import CrystalParser
from src.transformation.transformer import Transformer
from src.generation.oracle_xml_generator import OracleXMLGenerator


def main():
    # Parse the real Crystal XML
    parser = CrystalParser()
    model = parser.parse_file(Path('temp/SportsTeams_TorontoOnly.xml'))

    print(f'Parsed report: {model.name}')
    print(f'Queries: {len(model.queries)}')
    if model.queries:
        print(f'Query 1: {model.queries[0].name}')
        print(f'  Tables: {model.queries[0].tables}')
        print(f'  Columns: {len(model.queries[0].columns)}')
        for col in model.queries[0].columns[:5]:
            print(f'    - {col.name} ({col.data_type.value})')

    # Transform it
    transformer = Transformer()
    result = transformer.transform(model)

    print(f'\nTransformed:')
    print(f'Queries: {len(result.queries)}')
    if result.queries:
        query = result.queries[0]
        print(f'Query 1: {query["name"]}')
        print(f'  SQL: {query["sql"][:100]}...')
        print(f'  Columns: {len(query["columns"])}')
        for col in query["columns"][:5]:
            print(f'    - {col["name"]} ({col["data_type"]})')

    # Generate Oracle XML
    generator = OracleXMLGenerator()
    xml = generator.generate(result)

    # Save to file
    output_path = 'output/test_real.xml'
    with open(output_path, 'w') as f:
        f.write(xml)

    print(f'\nGenerated Oracle XML to: {output_path}')

    # Show the data section
    print('\n--- Data Section Preview ---')
    lines = xml.split('\n')
    in_data = False
    for line in lines:
        if '<data>' in line:
            in_data = True
        if in_data:
            print(line)
        if '</data>' in line:
            break


if __name__ == '__main__':
    main()
