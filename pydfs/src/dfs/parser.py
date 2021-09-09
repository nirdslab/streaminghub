import json
import logging
import os
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen

import jsonschema

from .errors import DoesNotMatchSchemaError, SchemaNotMentionedError, UnknownFileFormatError
from .types import DataSourceSpec, DataSetSpec, AnalyticSpec

logger = logging.getLogger()


def __fetch(path: str) -> dict:
  """
  Fetch a resource from the given path

  @param path:
  @return:
  """
  result = urlparse(path)
  content: dict
  if result.scheme == '':
    if not os.path.exists(path):
      abs_path = urljoin(os.getcwd(), path)
      if not os.path.exists(abs_path):
        raise FileNotFoundError(path, abs_path)
      path = abs_path
    logger.debug(f'Fetching: file://{path}')
    with open(path) as payload:
      try:
        content = json.load(payload)
      except json.JSONDecodeError:
        raise UnknownFileFormatError()
      logger.debug(f'Fetched: file://{path}')
  else:
    logger.debug(f'Fetching: {path}')
    with urlopen(path) as payload:
      try:
        content = json.load(payload)
      except json.JSONDecodeError:
        raise UnknownFileFormatError()
      logger.debug(f'Fetched: {path}')
  return content


def __fetch_spec(spec_uri: str) -> dict:
  """
  First, fetch the spec, validate against its schema.
  Next, recursively dereference and replace "sources" and values in the form "{uri}#/{path}".
  If external meta are loaded during this process, validate them as well.

  @param spec_uri: path for the JSON spec
  @return: dict containing the validated, dereferenced spec
  """

  def __find_target_value(v: str, base: dict, base_uri: str) -> any:
    [source_file, source_path] = v.strip().split('#/')
    source_dict = base if source_file == '' else __fetch_and_validate(urljoin(base_uri, source_file))
    # recurse and find the target value
    target_v = source_dict
    for key in source_path.split('/'):
      target_v = target_v[key]
    return target_v

  def __recursive_dereference(d: dict, base: dict, base_uri: str) -> None:
    for k, v in d.items():
      # recurse for dict
      if isinstance(v, dict):
        __recursive_dereference(v, base, base_uri)
      # iteratively dereference list items
      elif isinstance(v, list):
        # convert channels to dict
        if k == 'channels':
          x: str
          d[k] = {x.strip().rsplit('/', 1)[-1]: __find_target_value(x, base, base_uri) for x in v}
        else:
          for i, e in enumerate(v):
            if isinstance(e, dict):
              # recurse for dict
              __recursive_dereference(e, base, base_uri)
            elif isinstance(e, str) and len(e.strip().split('#/')) == 2:
              v[i] = __find_target_value(e, base, base_uri)
      # directly dereference strings
      elif isinstance(v, str) and len(v.strip().split('#/')) == 2:
        target = __find_target_value(v, base, base_uri)
        # convert index to dict
        if k == "index":
          d[k] = {v.strip().rsplit('/', 1)[-1]: target}
        else:
          d[k] = target

  def __fetch_and_validate(path) -> dict:
    spec = __fetch(path)
    # sanity check
    if '$schema' not in spec.keys():
      raise SchemaNotMentionedError()
    # load schema
    schema_uri = spec['$schema']
    schema = __fetch(schema_uri)
    try:
      validator = jsonschema.validators.Draft7Validator
      jsonschema.validate(spec, schema, validator)
    except jsonschema.ValidationError as e:
      raise DoesNotMatchSchemaError(e)
    # Task 1: first, dereference any sources
    if 'sources' in spec.keys():
      for k, v in spec['sources'].items():
        spec['sources'][k] = __fetch_and_validate(urljoin(path, v))
    # Task 2: next, dereference any JSON paths
    __recursive_dereference(spec, spec, path)
    # return the validated, dereferenced spec
    logger.debug(f'Validated Spec: {path}')
    return spec

  return __fetch_and_validate(spec_uri)


def get_datasource_spec(path: str) -> DataSourceSpec:
  data = __fetch_spec(path)
  spec = DataSourceSpec(d=data)
  logger.debug(f'Created DataSourceSpec: {path}')
  return spec


def get_dataset_spec(path: str):
  data = __fetch_spec(path)
  spec = DataSetSpec(d=data)
  logger.debug(f'Created DataSetSpec: {path}')
  return spec


def get_analytic_spec(path: str):
  data = __fetch_spec(path)
  spec = AnalyticSpec(d=data)
  logger.debug(f'Created AnalyticSpec: {path}')
  return spec
