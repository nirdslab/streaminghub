import logging
import os
from typing import Tuple, Dict, Any, Generator, Iterator

from core.types import DataSetSpec

logger = logging.getLogger()

QUESTION_SET_A = [1, 2, 3, 4, 5, 6, 7, 8, 9]
QUESTION_SET_B = [10, 11, 12, 13, 14, 15, 16, 17, 18]
RESOLUTION = [1920, 1080]

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]

SUMMARY = [
    # subject, diagnosis, question
    ('003', 'NTYP', 'SET_A'),
    ('005', 'NTYP', 'SET_B'),
    ('012', 'NTYP', 'SET_B'),
    ('014', 'NTYP', 'SET_A'),
    ('018', 'NTYP', 'SET_B'),
    ('021', 'NTYP', 'SET_A'),
    ('024', 'NTYP', 'SET_B'),
    ('026', 'NTYP', 'SET_A'),
    ('030', 'ADHD', 'SET_B'),
    ('032', 'NTYP', 'SET_B'),
    ('034', 'ADHD', 'SET_B'),
    ('035', 'ADHD', 'SET_A'),
    ('036', 'ADHD', 'SET_B'),
    ('037', 'ADHD', 'SET_A'),
    ('038', 'ADHD', 'SET_A'),
    ('047', 'ADHD', 'SET_B'),
]


def resolve(spec: DataSetSpec, **kwargs) -> Iterator[Tuple[DICT, str]]:
    # initialize empty parameters with default values from spec
    subject = kwargs.get('subject', spec.groups.get("subject").attributes)
    diagnosis = kwargs.get('diagnosis', spec.groups.get('diagnosis').attributes)
    question = kwargs.get('question', spec.groups.get("question").attributes)
    noise = kwargs.get('noise', spec.groups.get("noise").attributes)

    # filter by resolve values
    filtered = []
    for (d_subject, d_diagnosis, d_question) in SUMMARY:
        if d_subject in subject and d_diagnosis in diagnosis and d_question in question:
            filtered.append((d_subject, d_diagnosis, d_question))

    # yield resolved attributes and their file paths
    base_dir = os.path.dirname(__file__)
    for (f_subject, f_diagnosis, f_question_set) in filtered:
        if f_question_set == 'SET_A':
            f_questions = QUESTION_SET_A
        elif f_question_set == 'SET_B':
            f_questions = QUESTION_SET_B
        else:
            raise KeyError(f_question_set)
        for n in noise:
            for f_question in f_questions:
                filename = f'{f_subject}ADHD_AV_{n}{f_question}.csv'
                abs_path = os.path.join(base_dir, 'adhd_sin', filename)
                if os.path.exists(abs_path):
                    attrs = {"subject": f_subject, "diagnosis": f_diagnosis, "question": question, "noise": n, "resolution": RESOLUTION}
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
