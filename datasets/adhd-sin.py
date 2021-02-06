import pandas as pd


def find_data_slice(dataset_json, q_diagnosis=None, q_subject=None, q_noise=None, q_question=None):
    diagnosis = dataset_json["groups"]["diagnosis"]["values"]
    subjects = dataset_json["groups"]["subject"]["values"]
    noise = dataset_json["groups"]["subject"]["values"]
    question = dataset_json["groups"]["subject"]["values"]
    if q_diagnosis is not None:
        diagnosis = q_diagnosis
    if q_subject is not None:
        subjects = q_subject
    if q_noise is not None:
        noise = q_noise
    if q_question is not None:
        question = q_question
    return [diagnosis, subjects, noise, question]


def fetch_data_slice(data_slice):
    return
