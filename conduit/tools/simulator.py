#!/usr/bin/env python3

"""
This command-line executable simulates the datasets
stream of data in real-time, and generates a
datasets-stream based on the device specifications.

It can be used to replay an experimental setup from
the datasets that's already collected.


SCENE = 'SceneName'
DIAGNOSIS = "[Diagnosis]Value"
GENDER = "[Gender]Value"
TIMESTAMP = "RecordingTimestamp"
LEFT_GAZE_X = "GazePointLeftX (ADCSpx)"
LEFT_GAZE_Y = "GazePointLeftY (ADCSpx)"
LEFT_PUPIL_SIZE = "PupilLeft"
RIGHT_GAZE_X = "GazePointRightX (ADCSpx)"
RIGHT_GAZE_Y = "GazePointRightY (ADCSpx)"
RIGHT_PUPIL_SIZE = "PupilRight

"""

import asyncio
import random
import sys
import time
from typing import List

import pandas as pd

from core.io import get_meta_file
from core.lsl_outlet import create_outlet
from core.types import MetaFile, MetaStream

SYNTAX = "simulator [dataset-name] [participant_id] [noise_level] [question]"
RESOLUTION = [1920, 1080]  # 1920x1080
FREQ = 60  # 60 Hz
SCREEN_SIZE = 21  # 21 in
DISTANCE = 22.02  # 22.02 in
SOURCE_COLS = [
    'RecordingTimestamp',
    'GazePointLeftX (ADCSpx)',
    'GazePointLeftY (ADCSpx)',
    'PupilLeft',
    'GazePointRightX (ADCSpx)',
    'GazePointRightY (ADCSpx)',
    'PupilRight'
]
TARGET_COLS = [
    't',
    'l_x',
    'l_y',
    'l_d',
    'r_x',
    'r_y',
    'r_d'
]


async def emit(source_id: str, meta: MetaStream, idx: int, t_start: int):
    stream = meta.streams[idx]
    outlet = create_outlet(source_id, meta.device, stream)
    print(f'created stream: {stream.name}')
    while True:
        t = (time.time_ns() - t_start) * 1e-9
        outlet.push_sample([random.gauss(0, random.random() / 2) for _ in range(len(stream.channels))], t)
        # if stream frequency is zero, schedule next sample after a random time.
        # if not, schedule after (1 / f) time
        dt = (1. / stream.frequency) if stream.frequency > 0 else (random.randrange(0, 10) / 10.0)
        await asyncio.sleep(dt)


def load_meta_file(dataset: str, file_format: str) -> MetaFile:
    path = f'datasets/{dataset}/meta-file.{file_format}'
    assert file_format in ['json', 'xml'], f"Invalid File Format.\nExpected JSON or XML file"
    # load meta-file
    print(f'Loading meta-file: {path}...', end=' ', flush=True)
    meta_file = get_meta_file(path, file_format)
    print('DONE')
    return meta_file


def create_meta_streams(meta_file: MetaFile) -> List[MetaStream]:
    print(f'Creating meta-streams from meta-file...', end=' ', flush=True)
    meta_stream_infos = meta_file.sources.meta_streams
    meta_streams: List[MetaStream] = []
    for meta_stream_info in meta_stream_infos:
        meta_stream = MetaStream()
        # add meta-stream field information
        meta_stream.device = meta_stream_info.device
        meta_stream.fields = meta_file.fields
        meta_stream.streams = meta_stream_info.streams
        # info
        meta_stream.info = MetaStream.Info()
        meta_stream.info.version = meta_file.info.version
        meta_stream.info.checksum = meta_file.info.checksum
        # append to meta-stream list
        meta_streams.append(meta_stream)
    print('DONE')
    return meta_streams


def load_data_from_file(dataset: str, participant: int, noise_level: int, question: int) -> pd.DataFrame:
    path = f'datasets/{dataset}/data/{participant:03d}ADHD_AV_{noise_level}{question}.csv'
    print(f'Loading: {path}...', end=' ', flush=True)
    df = pd.read_csv(path)
    print(f'DONE')
    return df


async def begin_data_stream(meta: MetaStream, df: pd.DataFrame):
    t_start = time.time_ns()
    try:
        print("\n===========================")
        print('Starting datasets stream...')
        print(f'Device Name: {meta.device.model}, {meta.device.manufacturer} ({meta.device.category})')
        print("===========================\n")
        _id = '12345'
        # create a job for each stream defined in the meta-stream
        jobs = [emit(_id, meta, _idx, t_start) for _idx in range(len(meta.streams))]
        # start all jobs
        print('Data stream started\n')
        await asyncio.gather(*jobs)
    except KeyboardInterrupt:
        print('Interrupt received. Ending datasets stream...')
    finally:
        print('Data stream ended')


def main():
    # parse command-line args
    args = sys.argv
    assert len(args) == 5, f"Invalid Syntax.\nExpected: {SYNTAX}"
    dataset_name = args[1].strip()
    participant = int(args[2])
    noise_level = int(args[3])
    question = int(args[4])
    # print args
    print(f'Dataset: {dataset_name}')
    print(f'Participant: {participant:03d}')
    print(f'Noise Level: {noise_level}')
    print(f'Question: {question}\n')
    # load datasets
    meta_file = load_meta_file(dataset_name, 'json')
    meta_streams = create_meta_streams(meta_file)
    assert len(meta_streams) > 0, f"Meta-file does not have meta-streams"
    df = load_data_from_file(dataset_name, participant, noise_level, question)

    # temporary logic
    df = df[SOURCE_COLS].rename(columns={x: y for [x, y] in zip(SOURCE_COLS, TARGET_COLS)}).set_index('t')
    asyncio.get_event_loop().run_until_complete(begin_data_stream(meta_streams[0], df))


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
