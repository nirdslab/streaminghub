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
import importlib
import logging
import os
import random
import threading
from time import time_ns
from typing import Dict, Callable, Any, Generator

import numpy as np
from pylsl import StreamOutlet

from core.io import get_dataset_spec
from core.lsl_outlet import create_outlet
from core.types import DataSetSpec, DataSourceSpec, StreamInfo

DIGIT_CHARS = '0123456789'
SHUTDOWN_FLAG = threading.Event()
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.DEBUG)
logger = logging.getLogger()


def get_data_stream(spec: DataSetSpec, **kwargs) -> Generator[tuple[tuple, dict[str, float]], None, None]:
    module = importlib.import_module('datasets.adhd_sin')
    stream: Callable[[DataSetSpec, ...], Any] = getattr(module, 'stream')
    yield from stream(spec, **kwargs)


async def begin_streaming(dataset_spec: DataSetSpec, **kwargs):
    loop = asyncio.get_event_loop()
    data_sources = dataset_spec.sources
    # map each data source by a random id
    r_sources: Dict[str, DataSourceSpec] = {str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)]): data_source for data_source in data_sources.values()}
    # initialize all outlets
    r_outlets = {}
    for source_id in r_sources:
        source = r_sources[source_id]
        logger.info(f'Source [{source_id}]: {source.device.model}, {source.device.manufacturer} ({source.device.category})')
        logger.info(f'Source [{source_id}]: Initialization Started')
        source_outlets = {}
        for stream_id in source.streams:
            stream = source.streams[stream_id]
            outlet = create_outlet(source_id, source.device, stream)
            source_outlets[stream_id] = outlet
            logger.info(f'Source [{source_id}]: initialized stream [{stream.name}]')
        r_outlets[source_id] = source_outlets
        logger.info(f'Source [{source_id}]: Initialization Completed')

    # initiate data streaming via emit() function
    logger.debug(f'Started data streaming')
    tasks = []
    for source_id in r_sources:
        source = r_sources[source_id]
        for stream_id in source.streams:
            stream = source.streams[stream_id]
            task = loop.create_task(emit(r_outlets[source_id][stream_id], get_data_stream(dataset_spec, **kwargs), stream))
            tasks.append(task)
    await asyncio.gather(*tasks)
    logger.debug(f'Ended data streaming')


async def emit(outlet: StreamOutlet, data_stream: Generator[tuple[tuple, dict[str, float]], None, None], stream: StreamInfo):
    # get sampling frequency
    f = stream.frequency
    while True:
        t1 = time_ns() * 10e-9
        # graceful shutdown
        if SHUTDOWN_FLAG.is_set():
            logger.info(f'Shutdown initiated: stopped data stream')
            data_stream.close()
            break
        # calculate wait time (assign random wait time if frequency not set)
        dt = (1. / f) if f > 0 else (random.randrange(0, 10) / 10.0)
        # check if any consumers are available
        if outlet.have_consumers():
            # get relevant slice of data from sample
            [attrs, data] = next(data_stream)
            index = float(data[next(iter(stream.index))])  # assuming single-level indexes
            sample = [float(data[ch]) if data[ch] else np.nan for ch in stream.channels]
            # push sample if consumers are available
            outlet.push_sample(sample, index)
        # offset dt to account for cpu time
        t2 = time_ns() * 10e-9
        dt -= (t2 - t1)
        # sleep for dt to maintain stream frequency
        await asyncio.sleep(dt)


def main():
    # get default args
    default_dir = os.getenv("DATASET_DIR")
    default_name = os.getenv("DATASET_NAME")
    # create parser and parse args
    parser = argparse.ArgumentParser(prog='simulator.py')
    parser.add_argument('--dataset-dir', '-d', required=default_dir is None, default=default_dir)
    parser.add_argument('--dataset-name', '-n', required=default_name is None, default=default_name)
    args = parser.parse_args()
    # assign args to variables
    dataset_dir = args.dataset_dir or default_dir
    dataset_name = args.dataset_name or default_name
    # print args
    logger.info(f'Dataset Directory: {dataset_dir}')
    logger.info(f'Dataset Name: {dataset_name}')
    # get dataset spec
    dataset_spec = get_dataset_spec(f'{dataset_dir}/{dataset_name}.json', 'json')
    # get data sources
    assert len(dataset_spec.sources) > 0, f"Dataset does not have data sources"
    # spawn a worker thread for streaming
    logger.info('=== Begin streaming ===')
    worker = threading.Thread(target=asyncio.run, args=(begin_streaming(dataset_spec),))
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
