import core.io.json as json_parser
import core.io.xml as xml_parser
from core.errors import UnknownFileFormatError
from core.types import MetaStream, MetaFile, AnalyticStream


def get_meta_stream(path: str, file_type: str) -> MetaStream:
    if file_type == "json":
        return json_parser.meta_stream(path)
    elif file_type == "xml":
        return xml_parser.meta_stream(path)
    else:
        raise UnknownFileFormatError()


def get_meta_file(path: str, file_type: str) -> MetaFile:
    if file_type == "json":
        return json_parser.meta_file(path)
    elif file_type == "xml":
        return xml_parser.meta_file(path)
    else:
        raise UnknownFileFormatError()


def get_analytic_stream(path: str, file_type: str) -> AnalyticStream:
    if file_type == "json":
        return json_parser.analytic_stream(path)
    elif file_type == "xml":
        return xml_parser.analytic_stream(path)
    else:
        raise UnknownFileFormatError()
