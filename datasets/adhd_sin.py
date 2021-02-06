import os
from typing import List, Tuple, Iterator

from core.types import DataSetSpec

QUESTION_SET_A = [1, 2, 3, 4, 5, 6, 7, 8, 9]
QUESTION_SET_B = [10, 11, 12, 13, 14, 15, 16, 17, 18]

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


def resolve(spec: DataSetSpec, subject: list = None, diagnosis: list = None, question: list = None, noise: list = None, ) -> List[Tuple[Tuple, str]]:
    # initialize empty parameters with default values from spec
    subject = subject or spec.groups.get("subject").attributes
    diagnosis = diagnosis or spec.groups.get('diagnosis').attributes
    question = question or spec.groups.get("question").attributes
    noise = noise or spec.groups.get("noise").attributes

    # filter by resolve values
    filtered = []
    for (d_subject, d_diagnosis, d_question) in SUMMARY:
        if d_subject in subject and d_diagnosis in diagnosis and d_question in question:
            filtered.append((d_subject, d_diagnosis, d_question))

    # generate (and return) target file paths
    files = []
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
                    files.append(((f_subject, f_diagnosis, question, n), abs_path))
    return files


def stream(spec: DataSetSpec, subject: list = None, diagnosis: list = None, question: list = None, noise: list = None) -> Iterator[Tuple[Tuple, dict]]:
    files = resolve(spec, subject, diagnosis, question, noise)
    fields = spec.fields.keys()
    for attr, file in files:
        with open(file, 'r') as f:
            header = str(next(f)).strip().split(',')  # skip the header line of each file, and get column names
            mapping = {field: header.index(field) for field in fields}
            for row in f:
                data = row.strip().split(',')
                yield attr, {field: data[mapping[field]] for field in fields}
