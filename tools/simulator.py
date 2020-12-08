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
import os
import random
import sys
import threading
from typing import List

import pandas as pd

from core.io import get_meta_file
from core.lsl_outlet import create_outlet
from core.types import MetaFile, MetaStream

SYNTAX = "simulator [dataset-name] [participant_id] [noise_level] [question]"
RESOLUTION = [1920, 1080]  # 1920x1080
SCREEN_SIZE = 21  # 21 in
DISTANCE = 22.02  # 22.02 in
DIGIT_CHARS = '0123456789'
DATASET_DIR = os.getenv("DATASET_DIR")
SHUTDOWN_FLAG = threading.Event()


def load_meta_file(dataset: str, file_format: str, dataset_dir=DATASET_DIR) -> MetaFile:
    path = f'{dataset_dir}/{dataset}.{file_format}'
    assert file_format in ['json', 'xml'], f"Invalid File Format.\nExpected JSON or XML file"
    # load meta-file
    print(f'Loading meta-file: {path}...', end=' ', flush=True)
    meta_file = get_meta_file(path, file_format)
    print('DONE')
    return meta_file


def load_data_file(dataset: str, file_name: str, dataset_dir=DATASET_DIR) -> pd.DataFrame:
    path = f'{dataset_dir}/{dataset}/{file_name}'
    print(f'Loading: {path}...', end=' ', flush=True)
    df = pd.read_csv(path)
    print(f'DONE')
    return df


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


def create_streaming_task(meta: MetaStream, df: pd.DataFrame):
    # create an event loop and begin data stream
    inner_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(inner_loop)
    inner_loop.run_until_complete(begin_data_stream(meta, df))
    inner_loop.close()


async def begin_data_stream(meta: MetaStream, df: pd.DataFrame):
    _id = str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)])
    print(f'Created streaming task: {_id} - Device: {meta.device.model}, {meta.device.manufacturer} ({meta.device.category})', flush=True)
    # create a job for each stream defined in the meta-stream
    jobs = [emit(_id, meta, _idx, df) for _idx in range(len(meta.streams))]
    # start all jobs
    await asyncio.gather(*jobs)
    print(f'Ended streaming task: {_id}')


async def emit(source_id: str, meta: MetaStream, idx: int, df: pd.DataFrame):
    stream = meta.streams[idx]
    outlet = create_outlet(source_id, meta.device, stream)
    print(f'stream started - {stream.name}')
    # calculate low/high/range values of selected channels
    d_l = df[stream.channels].min().values
    d_h = df[stream.channels].max().values
    d_r = (d_h - d_l)
    f = stream.frequency
    n = df.index.size
    ptr = 0
    while not SHUTDOWN_FLAG.is_set():
        # calculate wait time
        dt = (1. / f) if f > 0 else (random.randrange(0, 10) / 10.0)
        # wait for consumers to show up
        if outlet.wait_for_consumers(dt):
            packet = df.iloc[ptr][stream.channels]
            [t, d] = packet.name, packet.values
            # normalize data
            d_n = (d - d_l) / d_r
            outlet.push_sample(d_n, t)
            # increment pointer (rolling)
            ptr = ptr + 1
            if ptr == n:
                print(f'end of stream reached - {stream.name}')
                return
            # sleep until next sample is due
            await asyncio.sleep(dt)
    print(f'stream terminated - {stream.name}')


def main():
    # parse command-line args
    args = sys.argv
    assert len(args) == 3, f"Invalid Syntax.\nExpected: {SYNTAX}"
    dataset_name = args[1].strip()
    file_name = args[2].strip()
    # print args
    print(f'Dataset: {dataset_name}')
    print(f'File: {file_name}')
    # load datasets
    meta_file = load_meta_file(dataset_name, 'json')
    idx_cols = next(filter(lambda x: x.type == "index", meta_file.links)).fields
    df = load_data_file(dataset_name, file_name).set_index(idx_cols)
    # create meta-streams
    meta_streams = create_meta_streams(meta_file)
    assert len(meta_streams) > 0, f"Meta-file does not have meta-streams"
    # spawn a thread for each meta-stream
    print('\n=== Initiating streaming tasks ===')
    threads = [threading.Thread(target=create_streaming_task, args=(meta, df)) for (i, meta) in enumerate(meta_streams)]
    # start streaming threads
    for t in threads:
        t.start()
    # add interrupt handler
    try:
        SHUTDOWN_FLAG.wait()
    except InterruptedError or KeyboardInterrupt:
        print('\nInterrupt received. Ending all stream tasks...\n')
        SHUTDOWN_FLAG.set()
        for t in threads:
            t.join()
    finally:
        print('\nAll streaming tasks ended\n')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
