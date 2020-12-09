#!/usr/bin/env python3

"""
This command-line executable simulates the datasets
stream of data in real-time, and generates a
datasets-stream based on the device specifications.

It can be used to replay an experimental setup from
the datasets that's already collected.
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

SYNTAX = "simulator [dataset_name] [file_name]"
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


async def begin_streaming(meta_streams: List[MetaStream], df: pd.DataFrame):
    tasks = []
    for (i, meta_stream) in enumerate(meta_streams):
        # create new id for each meta_stream
        source_id = str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)])
        for _idx in range(len(meta_stream.streams)):
            tasks.append(emit(source_id, meta_stream, _idx, df))
        print(f'Task [{source_id}]: Device: {meta_stream.device.model}, {meta_stream.device.manufacturer} ({meta_stream.device.category})', flush=True)
    print(f'Started all streaming tasks')
    await asyncio.gather(*tasks)
    print(f'Ended all streaming tasks')


async def emit(source_id: str, meta: MetaStream, idx: int, df: pd.DataFrame):
    stream = meta.streams[idx]
    outlet = create_outlet(source_id, meta.device, stream)
    print(f'Task [{source_id}]: stream started - {stream.name}')
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
        # check if any consumers are available
        if outlet.have_consumers():
            # push sample if consumers are available
            sample = df.iloc[ptr][stream.channels]
            [t, d] = sample.name, sample.values
            # normalize data
            d_n = (d - d_l) / d_r
            outlet.push_sample(d_n, t)
            # increment pointer (rolling)
            ptr = ptr + 1
            if ptr == n:
                print(f'Task [{source_id}]: end of stream reached - {stream.name}')
        # sleep until next sample is due
        await asyncio.sleep(dt)
    print(f'Task [{source_id}]: stream terminated - {stream.name}')


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
    # spawn a worker thread for streaming
    print('\n=== Begin streaming ===')
    worker = threading.Thread(target=asyncio.run, args=(begin_streaming(meta_streams, df),))
    worker.start()
    # add interrupt handler
    try:
        SHUTDOWN_FLAG.wait()
    except InterruptedError or KeyboardInterrupt:
        print('\nInterrupt received. Ending all stream tasks...\n')
        SHUTDOWN_FLAG.set()
    # wait for worker to close
    worker.join()
    print('\nAll streaming tasks ended\n')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
