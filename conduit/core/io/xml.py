from lxml import etree

from core.errors import DoesNotMatchSchemaError
from core.io import parser

__meta_file_schema_path = 'dfs/xml/dfs.xsd'
__meta_stream_schema_path = 'dfs/xml/dfs.xsd'
__analytic_stream_schema_path = 'dfs/xml/dfs.xsd'


def __load(path: str) -> etree:
    """
    Parse the content of an XML file into etree format

    :param path: path of the file
    :return: XML element tree
    """
    content: etree
    with open(path) as io:
        content = etree.parse(io)
    return content


def __read_spec(meta_path: str, schema_path: str) -> etree:
    """
    Load and Validate an XML element tree using the DFS schema.
    Throws a DocumentInvalid exception if its invalid.

    :param meta_path: path to XML file (metadata)
    :param schema_path: path to XSD file (schema)
    """
    meta = __load(meta_path)
    schema = __load(schema_path)
    if etree.XMLSchema(schema).validate(meta):
        return meta
    else:
        raise DoesNotMatchSchemaError()


def meta_stream(path: str):
    content = __read_spec(path, __meta_stream_schema_path)
    return parser.__parse_etree_into_meta_stream(content)


def meta_file(path: str):
    content = __read_spec(path, __meta_file_schema_path)
    return parser.__parse_etree_into_meta_file(content)


def analytic_stream(path: str):
    content = __read_spec(path, __analytic_stream_schema_path)
    return parser.__parse_etree_into_analytic_stream(content)
