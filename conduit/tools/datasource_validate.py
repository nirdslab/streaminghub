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

from dfs import get_datasource_spec
from dfs.errors import DoesNotMatchSchemaError

SYNTAX = "datasource_validate [path/to/datasource/spec]"


def validate_datasource_spec(path: str):
  print('Validating...')
  try:
    meta = get_datasource_spec(path, 'json')
    print(meta)
    print('Great work! Your DataSourceSpec is valid!')
  except DoesNotMatchSchemaError as e:
    print('ERROR - does not match schema', e, file=sys.stderr)


def main():
  # parse command-line args
  args = sys.argv
  assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
  meta_stream_path = args[1]
  print(f'File: {meta_stream_path}')
  file_format = meta_stream_path.rsplit('.', maxsplit=1)[-1].lower()
  assert file_format == 'json', f"Invalid File Format.\nExpected JSON"
  # validate schema
  if file_format == 'json':
    print('Found JSON schema')
    validate_datasource_spec(meta_stream_path)


if __name__ == '__main__':
  try:
    main()
  except AssertionError as e:
    print(f'Error: {e}', file=sys.stderr)
