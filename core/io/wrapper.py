import core.io.json as json_parser
import core.io.xml as xml_parser
from core.errors import UnknownFileFormatError
from core.types import Datasource, Dataset, Analytic


def get_meta_stream(path: str, file_type: str) -> Datasource:
    if file_type == "json":
        return json_parser.meta_stream(path)
    elif file_type == "xml":
        return xml_parser.meta_stream(path)
    else:
        raise UnknownFileFormatError()


def get_meta_file(path: str, file_type: str) -> Dataset:
    if file_type == "json":
        return json_parser.meta_file(path)
    elif file_type == "xml":
        return xml_parser.meta_file(path)
    else:
        raise UnknownFileFormatError()


def get_analytic_stream(path: str, file_type: str) -> Analytic:
    if file_type == "json":
        return json_parser.analytic_stream(path)
    elif file_type == "xml":
        return xml_parser.analytic_stream(path)
    else:
        raise UnknownFileFormatError()
