import json
import os

import jsonschema

from core.errors import DoesNotMatchSchemaError
from core.io import parser

__schema_path = f'{"/".join(os.path.dirname(__file__).split("/")[:-2])}/dfs/json/dfs.jsd'


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


def __read_spec(meta_path: str, schema_path: str, schema_name) -> dict:
    """
    Validate an XML element tree using the DFS schema.
    Throws a DocumentInvalid exception if it is not valid

    :param meta_path: path to JSON file
    :param schema_path: path to JSON schema file
    """
    meta = __load(meta_path)
    schema = __load(schema_path)
    schema["$ref"] = f"#/definitions/{schema_name}"
    try:
        jsonschema.validate(meta, schema)
        return meta
    except jsonschema.ValidationError as e:
        raise DoesNotMatchSchemaError()


def meta_stream(path: str):
    content = __read_spec(path, __schema_path, "meta-stream")
    return parser.__parse_dict_into_meta_stream(content)


def meta_file(path: str):
    content = __read_spec(path, __schema_path, "meta-file")
    return parser.__parse_dict_into_meta_file(content)


def analytic_stream(path: str):
    content = __read_spec(path, __schema_path, "analytic-stream")
    return parser.__parse_dict_into_analytic_stream(content)
