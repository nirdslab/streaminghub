#!/usr/bin/env python3

"""
This command-line executable simulates the datasets
stream of data in real-time, and generates a
datasets-stream based on the device specifications.

It can be used to replay an experimental setup from
the datasets that's already collected.
"""

import logging
import argparse
import asyncio
import os
import random
import threading
from typing import List
import pandas as pd
from core.io import get_meta_file
from core.lsl_outlet import create_outlet
from core.types import Dataset, Datasource

DIGIT_CHARS = '0123456789'
SHUTDOWN_FLAG = threading.Event()
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()


def load_meta_file(dataset_dir: str, dataset_name: str, file_format: str) -> Dataset:
    path = f'{dataset_dir}/{dataset_name}.{file_format}'
    logger.debug(f'Loading meta-file: {path}')
    meta_file = get_meta_file(path, file_format)
    logger.debug(f'Loaded meta-file: {path}')
    return meta_file


def load_data_file(dataset_dir: str, dataset: str, file_name: str) -> pd.DataFrame:
    path = f'{dataset_dir}/{dataset}/{file_name}'
    logger.debug(f'Loading data-file: {path}')
    df = pd.read_csv(path)
    logger.debug(f'Loaded data-file: {path}')
    return df


def create_meta_streams(meta_file: Dataset) -> List[Datasource]:
    logger.debug(f'Creating meta-streams from meta-file')
    meta_stream_infos = meta_file.sources.sources
    meta_streams: List[Datasource] = []
    for meta_stream_info in meta_stream_infos:
        meta_stream = Datasource()
        # add meta-stream field information
        meta_stream.device = meta_stream_info.device
        meta_stream.fields = meta_file.fields
        meta_stream.streams = meta_stream_info.streams
        # info
        meta_stream.info = Datasource.Info()
        meta_stream.info.version = meta_file.info.version
        meta_stream.info.checksum = meta_file.info.checksum
        # append to meta-stream list
        meta_streams.append(meta_stream)
    logger.debug(f'Created meta-streams from meta-file')
    return meta_streams


async def begin_streaming(meta_streams: List[Datasource], df: pd.DataFrame):
    tasks = []
    for meta_stream in meta_streams:
        # create new id for each meta_stream
        source_id = str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)])
        for stream in meta_stream.streams:
            tasks.append(emit(source_id, meta_stream.device, stream, df))
        logger.info(f'Task [{source_id}]: Device: {meta_stream.device.model}, {meta_stream.device.manufacturer} ({meta_stream.device.category})')
    logger.debug(f'Started all streaming tasks')
    await asyncio.gather(*tasks)
    logger.debug(f'Ended all streaming tasks')


async def emit(source_id: str, device: Datasource.DeviceInfo, stream: Datasource.StreamInfo, df: pd.DataFrame):
    outlet = create_outlet(source_id, device, stream)
    logger.info(f'Task [{source_id}]: stream started - {stream.name}')
    # calculate low/high/range values of selected channels
    d_l = df[stream.channels].min().values
    d_h = df[stream.channels].max().values
    d_r = (d_h - d_l)
    f = stream.frequency
    n = df.index.size
    ptr = 0
    while True:
        # graceful shutdown
        if SHUTDOWN_FLAG.is_set():
            logger.info(f'Task [{source_id}]: stream terminated - {stream.name}')
            break
        # end of stream
        if ptr == n:
            logger.info(f'Task [{source_id}]: end of stream reached - {stream.name}')
            break
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
        # sleep until next sample is due
        await asyncio.sleep(dt)


def main():
    # get default args
    default_dir = os.getenv("DATASET_DIR")
    default_name = os.getenv("DATASET_NAME")
    default_file = os.getenv("DATASET_FILE")
    # create parser and parse args
    parser = argparse.ArgumentParser(prog='simulator.py')
    parser.add_argument('--dataset-dir', '-d', required=default_dir is None, default=default_dir)
    parser.add_argument('--dataset-name', '-n', required=default_name is None, default=default_name)
    parser.add_argument('--dataset-file', '-f', required=default_file is None, default=default_file)
    args = parser.parse_args()
    # assign args to variables
    dataset_dir = args.dataset_dir or default_dir
    dataset_name = args.dataset_name or default_name
    dataset_file = args.dataset_file or default_file
    # print args
    logger.info(f'Dataset Directory: {dataset_dir}')
    logger.info(f'Dataset Name: {dataset_name}')
    logger.info(f'Dataset File: {dataset_file}')
    # load datasets
    meta_file = load_meta_file(dataset_dir, dataset_name, 'json')
    idx_cols = next(filter(lambda x: x.type == "index", meta_file.links)).fields
    df = load_data_file(dataset_dir, dataset_name, dataset_file).set_index(idx_cols)
    # create meta-streams
    meta_streams = create_meta_streams(meta_file)
    assert len(meta_streams) > 0, f"Meta-file does not have meta-streams"
    # spawn a worker thread for streaming
    logger.info('=== Begin streaming ===')
    worker = threading.Thread(target=asyncio.run, args=(begin_streaming(meta_streams, df),))
    try:
        worker.start()
        worker.join()
    except (KeyboardInterrupt, InterruptedError):
        logger.info('Interrupt received. Ending all stream tasks..')
        # set flag for graceful shutdown
        SHUTDOWN_FLAG.set()
    # wait for worker to close
    worker.join()
    logger.info('All streaming tasks ended')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        logger.error(f'Error: {e}')
