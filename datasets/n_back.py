import logging
import os
from typing import List, Tuple, Dict, Any, Generator

from core.types import DataSetSpec

logger = logging.getLogger()


def resolve(spec: DataSetSpec, **kwargs) -> List[Tuple[Dict[str, Any], str]]:
    # initialize empty parameters with default values from spec
    subject = kwargs.get('subject', spec.groups.get("subject").attributes)
    xtype = kwargs.get('xtype', spec.groups.get('xtype').attributes)
    task = kwargs.get('task', spec.groups.get("task").attributes)

    # filter by resolve values
    filtered = []
    for d_subject in subject:
        for d_xtype in xtype:
            for d_task in task:
                filtered.append((d_subject, d_xtype, d_task))

    # generate (and return) target file paths
    files = []
    base_dir = os.path.dirname(__file__)
    for (f_subject, f_xtype, f_task) in filtered:
        filename = f'{f_subject}-{f_xtype}-{f_task}.csv'
        abs_path = os.path.join(base_dir, 'n_back', filename)
        if os.path.exists(abs_path):
            attrs = {"subject": f_subject, "xtype": f_xtype, "task": f_task}
            files.append((attrs, abs_path))
    return files


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
