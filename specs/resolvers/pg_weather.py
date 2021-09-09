import logging
import os
from typing import Tuple, Dict, Any, Generator, Iterator

from dfs.types import DataSetSpec

logger = logging.getLogger()

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]


def resolve(spec: DataSetSpec, **kwargs) -> Iterator[Tuple[DICT, str]]:
  # initialize empty parameters with default values from spec
  state = kwargs.get('state', spec.groups.get('state').attributes)
  city = kwargs.get('city', spec.groups.get('city').attributes)
  logger.info(f"requested: "
              f"[State]:{','.join(state):.40}{'...' * bool(','.join(state)[40:])}, "
              f"[City]:{','.join(city):.40}{'...' * bool(','.join(city)[40:])}")

  # filter by resolve values
  filtered = ((s, c) for s in state for c in city)

  # generate (and yield) target file paths
  base_dir = os.getenv("STREAMINGHUB_DATA_DIR")
  for (f_state, f_city) in filtered:
    filename = f'{f_state}-{f_city}.csv'
    abs_path = os.path.join(base_dir, 'pg_weather', filename)
    if os.path.isfile(abs_path):
      attrs = {"city": f_city, "state": f_state}
      yield attrs, abs_path


def d_stream(file: str, fields: Iterator[str]) -> DICT_GENERATOR:
  with open(file, 'r') as f:
    logger.debug('Opened file: %s', file)
    header = str(next(f)).strip().split(',')  # skip the header line of each file, and get column names
    mapping = {field: header.index(field) for field in fields}
    assert -1 not in mapping.values(), "Some headers not found"
    for row in f:
      row_data = row.strip().split(',')
      yield {field: row_data[mapping[field]] for field in fields}
  logger.debug('Closed file: %s', file)


def stream(spec: DataSetSpec, **kwargs) -> Iterator[Tuple[DICT, DICT_GENERATOR]]:
  files = resolve(spec, **kwargs)
  fields = [*spec.fields.keys()]
  return [(attrs, d_stream(file, fields)) for attrs, file in files]
