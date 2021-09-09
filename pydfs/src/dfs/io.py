from .errors import UnknownFileFormatError
from .parser import datasource, dataset, analytic
from .types import DataSourceSpec, DataSetSpec, AnalyticSpec


def get_datasource_spec(path: str, file_type: str) -> DataSourceSpec:
  if file_type == "json":
    return datasource(path)
  else:
    raise UnknownFileFormatError()


def get_dataset_spec(path: str, file_type: str) -> DataSetSpec:
  if file_type == "json":
    return dataset(path)
  else:
    raise UnknownFileFormatError()


def get_analytic_spec(path: str, file_type: str) -> AnalyticSpec:
  if file_type == "json":
    return analytic(path)
  else:
    raise UnknownFileFormatError()
