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
import random
import sys
import time

from core.io import get_meta_stream
from core.lsl_outlet import create_outlet
from core.types import MetaStream

SYNTAX = "data-stream-generator [schema_file]"


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


async def begin_data_stream(meta: MetaStream):
    t_start = time.time_ns()
    try:
        print('Starting data stream...')
        print(f'Device Name: {meta.device.model}, {meta.device.manufacturer} ({meta.device.category})')
        _id = '12345'
        # create a job for each stream defined in the meta-stream
        jobs = [emit(_id, meta, _idx, t_start) for _idx in range(len(meta.streams))]
        # start all jobs
        print('Data stream started')
        await asyncio.gather(*jobs)
    except KeyboardInterrupt:
        print('Interrupt received. Ending data stream...')
    finally:
        print('Data stream ended')


def main():
    # parse command-line args
    args = sys.argv
    assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
    meta_stream_path = args[1]
    print(f'File: {meta_stream_path}')
    file_format = meta_stream_path.rsplit('.', maxsplit=1)[-1].lower()
    assert file_format in ['json', 'xml'], f"Invalid File Format.\nExpected JSON or XML file"
    # load meta-stream
    print('Loading meta-stream...')
    meta_stream = get_meta_stream(meta_stream_path, file_format)
    print('Loaded')
    # start data stream
    asyncio.get_event_loop().run_until_complete(begin_data_stream(meta_stream))


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
