#!/usr/bin/env python3

"""
This command-line executable program accepts a
meta-stream as an input, and generates a
data-stream based on the given meta-stream spec.

It can be used for testing on meta-streams and
data-streams without the need for an actual
sensory device.
"""

import asyncio
import logging
import random
import sys
import time

from dfs import create_outlet, get_datasource_spec, DataSourceSpec

SYNTAX = "datasource_simulate [path/to/datasource/spec]"
DIGIT_CHARS = '0123456789'

logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()


async def emit(source_id: str, spec: DataSourceSpec, stream_id: str):
  stream = spec.streams[stream_id]
  f = stream.frequency
  outlet = create_outlet(source_id, spec.device, stream)
  logger.info(f'created stream: {stream.name}')
  while True:
    # calculate dt from f. if f=0, assign a random dt
    dt = (1. / f) if f > 0 else (random.randrange(0, 10) / 10.0)
    if outlet.have_consumers():
      t1 = time.time_ns() * 1e-9
      sample = [random.gauss(0, random.random() / 2) for _ in range(len(stream.channels))]
      logger.debug(f'DataSource [{source_id}]: T={t1}, Sample={sample}')
      outlet.push_sample(sample, t1)
      # offset dt by cpu time
      t2 = time.time_ns() * 1e-9
      dt -= (t2 - t1)
    await asyncio.sleep(dt)


async def begin_streaming_random_data(spec: DataSourceSpec):
  source_id = str.join('', [random.choice(DIGIT_CHARS) for _ in range(5)])
  try:
    logger.info(
      f'DataSource [{source_id}]: Device: {spec.device.model}, {spec.device.manufacturer} ({spec.device.category})')
    # create a job for each stream defined in the meta-stream
    jobs = [emit(source_id, spec, stream_id) for stream_id in spec.streams]
    # start all jobs
    logger.info(f'DataSource [{source_id}]: Started streams')
    await asyncio.gather(*jobs)
  except KeyboardInterrupt:
    logger.info(f'DataSource [{source_id}]: Interrupt received. Closing streams...')
  finally:
    logger.info(f'DataSource [{source_id}]: Closed streams')


def main():
  # parse command-line args
  args = sys.argv
  assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
  spec_path = args[1]
  logger.info(f'DataSourceSpec: {spec_path}')
  file_format = spec_path.rsplit('.', maxsplit=1)[-1].lower()
  assert file_format == 'json', f"Invalid File Format.\nExpected JSON"
  # load DataSourceSpec
  logger.info('Loading DataSourceSpec...')
  spec = get_datasource_spec(spec_path, file_format)
  logger.info('Loaded')
  # start data stream
  asyncio.get_event_loop().run_until_complete(begin_streaming_random_data(spec))


if __name__ == '__main__':
  try:
    main()
  except AssertionError as e:
    logger.error(f'Error: {e}', file=sys.stderr)
