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
import sys
import threading
from time import time_ns
from typing import Dict, Callable, Any, Generator, Iterator, Tuple

import numpy as np
from pylsl import StreamOutlet

from dfs import get_data_dir, get_datasource_dir, get_dataset_dir, get_analytic_dir, get_meta_dir
from dfs import get_dataset_spec, create_outlet, DataSetSpec, DataSourceSpec, StreamInfo

DIGIT_CHARS = '0123456789'
SHUTDOWN_FLAG = threading.Event()
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()


def get_attrs_and_streams(spec: DataSetSpec, dataset_name: str, **kwargs) -> Iterator[
  Tuple[Dict[str, Any], Generator[Dict[str, float], None, None]]]:
  if get_meta_dir() not in sys.path:
    sys.path.append(get_meta_dir())
  resolver = importlib.import_module(f'resolvers.{dataset_name}')
  stream: Callable[[DataSetSpec, ...], Any] = getattr(resolver, 'stream')
  yield from stream(spec, **kwargs)


async def begin_streaming(dataset_spec: DataSetSpec, dataset_name: str, **kwargs):
  loop = asyncio.get_event_loop()
  data_sources = dataset_spec.sources
  # map each data source by a random id
  r_sources: Dict[str, DataSourceSpec] = {str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)]): data_source for
                                          data_source in data_sources.values()}
  # initiate data streaming via emit() function
  tasks = []
  for source_id in r_sources:
    source = r_sources[source_id]
    logger.info(f'Source [{source_id}]: {source.device.model}, {source.device.manufacturer} ({source.device.category})')
    for stream_id in source.streams:
      stream_info = source.streams[stream_id]
      logger.info(f'Source [{source_id}]: initialized stream [{stream_info.name}]')
      # TODO for now sending everything in same outlet, later find a way to split outlets by attrs (or create a new outlet for each distinct attr)
      for attrs, data_stream in get_attrs_and_streams(dataset_spec, dataset_name, **kwargs):
        # create outlet for every nested attr, and create hierarchy
        outlet = create_outlet(source_id, source.device, stream_info, attrs)
        task = loop.create_task(emit(outlet, data_stream, stream_info))
        tasks.append(task)
    logger.info(f'Source [{source_id}]: Initialization Completed')
  await asyncio.gather(*tasks)
  logger.info(f'Ended data streaming')


async def emit(outlet: StreamOutlet, data_stream: Generator[Dict[str, float], None, None], stream: StreamInfo):
  # get sampling frequency
  f = stream.frequency
  # calculate wait time (assign random wait time if frequency not set)
  dt = (1. / f) if f > 0 else (random.randrange(0, 10) / 10.0)
  # time when last sample was sent
  prev_ts = None
  # time taken between last two samples (ideally dt, but in practice > dt)
  prev_dt = dt
  while True:
    # graceful shutdown
    if SHUTDOWN_FLAG.is_set():
      logger.debug(f'Shutdown initiated: stopped data stream')
      data_stream.close()
      break
    # check if any consumers are available
    if outlet.have_consumers():
      # get relevant slice of data from sample
      data = next(data_stream, None)
      # end of data stream
      if data is None:
        logger.info(f'Reached end of data stream')
        break
      index = float(data[next(iter(stream.index))])  # assuming single-level indexes
      sample = [float(data[ch]) if data[ch] else np.nan for ch in stream.channels]
      if not all([i == np.nan for i in sample]):
        ts = time_ns() * 1e-9
        # push sample if consumers are available, and data exists
        outlet.push_sample(sample, index)
        # update prev_dt
        if prev_ts is not None:
          prev_dt = ts - prev_ts
        # update prev_ts
        prev_ts = ts
    # sleep for dt + correction to maintain stream frequency
    await asyncio.sleep(dt + (dt - prev_dt))


def parse_attrs(attrs: str) -> dict:
  return {attr.split("=", 1)[0]: attr.split("=", 1)[1].split(",") for attr in attrs.split(' ')} if attrs else {}


def main():
  # get default args
  # create parser and parse args
  parser = argparse.ArgumentParser(prog='datasource_replay.py')
  # required args
  parser.add_argument('--dataset-name', '-n', required=True)
  # optional args
  parser.add_argument('--attributes', '-a', required=False)
  parser.add_argument('--data-dir', '-d', required=False)
  parser.add_argument('--meta-dir', '-m', required=False)
  # parse all args
  args = parser.parse_args()
  dataset_name = args.dataset_name
  # update environment variables if directories are overridden
  if args.data_dir is not None:
    logger.info(f'changing streaminghub data directory to: {args.data_dir}')
    os.environ['STREAMINGHUB_DATA_DIR'] = args.data_dir
    os.putenv('STREAMINGHUB_DATA_DIR', args.data_dir)
  if args.meta_dir is not None:
    logger.info(f'changing streaminghub meta directory to: {args.meta_dir}')
    os.putenv('STREAMINGHUB_META_DIR', args.meta_dir)
    os.environ['STREAMINGHUB_META_DIR'] = args.meta_dir
  # print args
  logger.info(f'Dataset Name: {dataset_name}')
  logger.info(f'Data Directory: {get_data_dir()}')
  logger.info(f'Datasource Meta Directory: {get_datasource_dir()}')
  logger.info(f'Dataset Meta Directory: {get_dataset_dir()}')
  logger.info(f'Analytic Meta Directory: {get_analytic_dir()}')
  # get dataset spec
  dataset_spec = get_dataset_spec(dataset_name)
  # get data sources
  assert len(dataset_spec.sources) > 0, f"Dataset does not have data sources"
  # spawn a worker thread for streaming
  logger.info('=== Begin streaming ===')
  worker = threading.Thread(
    target=asyncio.run,
    args=(begin_streaming(dataset_spec, dataset_name, **parse_attrs(args.attributes)),)
  )
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