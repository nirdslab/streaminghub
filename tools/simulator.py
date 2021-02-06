#!/usr/bin/env python3

"""
This command-line executable simulates the datasets
stream of data in real-time, and generates a
datasets-stream based on the device specifications.

It can be used to replay an experimental setup from
the datasets that's already collected.
"""

import argparse
import asyncio
import logging
import os
import random
import threading
from typing import Dict

import pandas as pd

from core.io import get_dataset_spec
from core.lsl_outlet import create_outlet
from core.types import DataSetSpec, DataSourceSpec, DeviceInfo, StreamInfo

DIGIT_CHARS = '0123456789'
SHUTDOWN_FLAG = threading.Event()
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.DEBUG)
logger = logging.getLogger()


def load_dataset_spec(dataset_dir: str, dataset_name: str, file_format: str) -> DataSetSpec:
    path = f'{dataset_dir}/{dataset_name}.{file_format}'
    meta_file = get_dataset_spec(path, file_format)
    return meta_file


def load_data(dataset_dir: str, dataset: str, file_name: str) -> pd.DataFrame:
    path = f'{dataset_dir}/{dataset}/{file_name}'
    logger.debug(f'Loading data of dataset: {path}')
    df = pd.read_csv(path)
    logger.debug(f'Loaded data of dataset: {path}')
    return df


async def begin_streaming(data_sources: Dict[str, DataSourceSpec], df: pd.DataFrame):
    tasks = []
    for data_source in data_sources.values():
        # create new id for each data source
        data_source_id = str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)])
        device = data_source.device
        for stream in data_source.streams.values():
            tasks.append(emit(data_source_id, device, stream, df))
        logger.info(f'Task [{data_source_id}]: Device: {device.model}, {device.manufacturer} ({device.category})')
    logger.debug(f'Started all streaming tasks')
    await asyncio.gather(*tasks)
    logger.debug(f'Ended all streaming tasks')


async def emit(source_id: str, device: DeviceInfo, stream: StreamInfo, df: pd.DataFrame):
    df = df.set_index(list(stream.index.keys()))
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
    # load dataset spec
    dataset_spec = load_dataset_spec(dataset_dir, dataset_name, 'json')
    # idx_cols = next(filter(lambda x: x.type == "index", dataset_spec.links)).fields
    df = load_data(dataset_dir, dataset_name, dataset_file)
    # get data sources
    data_sources = dataset_spec.sources
    assert len(data_sources) > 0, f"Dataset does not have data sources"
    # spawn a worker thread for streaming
    logger.info('=== Begin streaming ===')
    worker = threading.Thread(target=asyncio.run, args=(begin_streaming(data_sources, df),))
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
