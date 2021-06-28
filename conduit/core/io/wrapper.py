import core.io.parser as parser
from core.errors import UnknownFileFormatError
from core.types import DataSourceSpec, DataSetSpec, AnalyticSpec


def get_datasource_spec(path: str, file_type: str) -> DataSourceSpec:
    if file_type == "json":
        return parser.datasource(path)
    else:
        raise UnknownFileFormatError()


def get_dataset_spec(path: str, file_type: str) -> DataSetSpec:
    if file_type == "json":
        return parser.dataset(path)
    else:
        raise UnknownFileFormatError()


def get_analytic_spec(path: str, file_type: str) -> AnalyticSpec:
    if file_type == "json":
        return parser.analytic(path)
    else:
        raise UnknownFileFormatError()
