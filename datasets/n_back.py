import logging
import os
from typing import Tuple, Dict, Any, Generator, Iterator

from core.types import DataSetSpec

logger = logging.getLogger()


def resolve(spec: DataSetSpec, **kwargs) -> Iterator[Tuple[Dict[str, Any], str]]:
    # initialize empty parameters with default values from spec
    subject = kwargs.get('subject', spec.groups.get('subject').attributes)
    mode = kwargs.get('mode', spec.groups.get('mode').attributes)
    task = kwargs.get('task', spec.groups.get('task').attributes)
    position = kwargs.get('position', spec.groups.get('position').attributes)

    # filter by resolve values
    filtered = ((s, m, t, p) for s in subject for m in mode for t in task for p in position)

    # generate (and yield) target file paths
    base_dir = os.path.dirname(__file__)
    for (f_subject, f_mode, f_task, f_position) in filtered:
        filename = f'{f_subject}-{f_mode}-{f_task}-{f_position}.csv'
        abs_path = os.path.join(base_dir, 'n_back', filename)
        if os.path.exists(abs_path):
            attrs = {"subject": f_subject, "mode": f_mode, "task": f_task, "position": f_position}
            yield attrs, abs_path


def stream(spec: DataSetSpec, **kwargs) -> Generator[Tuple[Dict[str, Any], Dict[str, Any]], None, None]:
    files = resolve(spec, **kwargs)
    fields = spec.fields.keys()
    for attrs, file in files:
        with open(file, 'r') as f:
            logger.debug('Opened file: %s', file)
            header = str(next(f)).strip().split(',')  # skip the header line of each file, and get column names
            mapping = {field: header.index(field) for field in fields}
            assert -1 not in mapping.values(), "Some headers not found"
            for row in f:
                data_list = row.strip().split(',')
                data_dict = {field: data_list[mapping[field]] for field in fields}
                yield attrs, data_dict
        logger.debug('Closed file: %s', file)
