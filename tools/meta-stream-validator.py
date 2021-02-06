#!/usr/bin/env python3

"""
This command-line executable program accepts a
meta-stream as an input, and checks for its
validity.

It can be used for testing meta-streams and
finding whether they are compliant with the
proposed standards.
"""

import sys

from core.errors import DoesNotMatchSchemaError
from core.io import get_datasource_spec

SYNTAX = "meta-stream-validator [path_to_meta_stream]"


def validate_xml_schema(path: str):
    print('Validating...')
    try:
        meta = get_datasource_spec(path, 'xml')
        print(meta)
        print('Great work! Your meta-stream is valid!')
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)


def validate_json_schema(path: str):
    print('Validating...')
    try:
        meta = get_datasource_spec(path, 'json')
        print(meta)
        print('Great work! Your meta-stream is valid!')
    except DoesNotMatchSchemaError as e:
        print('ERROR - does not match schema', file=sys.stderr)


def main():
    # parse command-line args
    args = sys.argv
    assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
    meta_stream_path = args[1]
    print(f'File: {meta_stream_path}')
    file_format = meta_stream_path.rsplit('.', maxsplit=1)[-1].lower()
    assert file_format in ['json', 'xml'], f"Invalid File Format.\nExpected JSON or XML file"
    # validate schema
    if file_format == 'xml':
        print('Found XML schema')
        validate_xml_schema(meta_stream_path)
    if file_format == 'json':
        print('Found JSON schema')
        validate_json_schema(meta_stream_path)


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
