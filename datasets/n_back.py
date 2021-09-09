import logging
import os
from typing import Tuple, Dict, Any, Generator, Iterator

from core.types import DataSetSpec

logger = logging.getLogger()

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]


def resolve(spec: DataSetSpec, **kwargs) -> Iterator[Tuple[DICT, str]]:
  # initialize empty parameters with default values from spec
  subject = kwargs.get('subject', spec.groups.get('subject').attributes)
  mode = kwargs.get('mode', spec.groups.get('mode').attributes)
  task = kwargs.get('task', spec.groups.get('task').attributes)
  position = kwargs.get('position', spec.groups.get('position').attributes)
  logger.info(f"requested: "
              f"[Subject]:{','.join(subject):.40}{'...' * bool(','.join(subject)[40:])}, "
              f"[Mode]:{','.join(mode):.40}{'...' * bool(','.join(mode)[40:])}, "
              f"[Task]:{','.join(task):.40}{'...' * bool(','.join(task)[40:])}, "
              f"[Position]:{','.join(position):.40}{'...' * bool(','.join(position)[40:])}")

  # filter by resolve values
  filtered = ((s, m, t, p) for s in subject for m in mode for t in task for p in position)

  # generate (and yield) target file paths
  base_dir = os.path.dirname(__file__)
  for (f_subject, f_mode, f_task, f_position) in filtered:
    filename = f'{f_subject}-{f_mode}-{f_task}-{f_position}.csv'
    abs_path = os.path.join(base_dir, 'n_back', filename)
    if os.path.isfile(abs_path):
      attrs = {"subject": f_subject, "mode": f_mode, "task": f_task, "position": f_position}
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
