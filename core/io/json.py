import json

import jsonschema

from core.errors import DoesNotMatchSchemaError
from core.io import parser

__meta_file_schema_path = 'dfs/json/meta-file.jsd'
__meta_stream_schema_path = 'dfs/json/meta-stream.jsd'
__analytic_stream_schema_path = 'dfs/json/analytic-stream.jsd'


def __load(path: str) -> dict:
    """
    Parse the content of a JSON file into dict format

    :param path: path of the file
    :return: JSON object
    """
    content: dict
    with open(path) as io:
        content = json.load(io)
    return content


def __read_spec(meta_path: str, schema_path: str) -> dict:
    """
    Validate an XML element tree using the DFS schema.
    Throws a DocumentInvalid exception if it is not valid

    :param meta_path: path to JSON file
    :param schema_path: path to JSON schema file
    """
    meta = __load(meta_path)
    schema = __load(schema_path)
    if jsonschema.validate(meta, schema):
        return meta
    else:
        raise DoesNotMatchSchemaError()


def meta_stream(path: str):
    content = __read_spec(path, __meta_stream_schema_path)
    return parser.__parse_dict_into_meta_stream(content)


def meta_file(path: str):
    content = __read_spec(path, __meta_file_schema_path)
    return parser.__parse_dict_into_meta_file(content)


def analytic_stream(path: str):
    content = __read_spec(path, __analytic_stream_schema_path)
    return parser.__parse_dict_into_analytic_stream(content)
