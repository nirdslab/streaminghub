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

import streaminghub_pydfds as dfds
import streaminghub_datamux as datamux
from rich.logging import RichHandler

SYNTAX = "datasource_simulate [path/to/datasource/spec]"

logger = logging.getLogger(__name__)
api = datamux.API()


async def emit(source_id: str, spec: dfds.Collection, stream_id: str):
    stream = spec.streams[stream_id]
    f = stream.frequency
    outlet = api.create_outlet_for_stream(source_id, spec.device, stream_id, stream)
    logger.info(f"created stream: {stream.name}")
    while True:
        # calculate dt from f. if f=0, assign a random dt
        dt = (1.0 / f) if f > 0 else (random.randrange(0, 10) / 10.0)
        if outlet.have_consumers():
            t1 = time.time_ns() * 1e-9
            sample = [random.gauss(0, random.random() / 2) for _ in range(len(stream.channels))]
            logger.debug(f"DataSource [{source_id}]: T={t1}, Sample={sample}")
            outlet.push_sample(sample, t1)
            # offset dt by cpu time
            t2 = time.time_ns() * 1e-9
            dt -= t2 - t1
        await asyncio.sleep(dt)


async def begin_streaming_random_data(spec: dfds.Collection):
    source_id = datamux.gen_randseq()
    try:
        logger.info(
            f"DataSource [{source_id}]: Device: {spec.device.model}, {spec.device.manufacturer} ({spec.device.category})"
        )
        # create a job for each stream defined in the meta-stream
        jobs = [emit(source_id, spec, stream_id) for stream_id in spec.streams]
        # start all jobs
        logger.info(f"DataSource [{source_id}]: Started streams")
        await asyncio.gather(*jobs)
    except KeyboardInterrupt:
        logger.info(f"DataSource [{source_id}]: Interrupt received. Closing streams...")
    finally:
        logger.info(f"DataSource [{source_id}]: Closed streams")


def main():
    # parse command-line args
    args = sys.argv
    assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
    collection_name = args[1]
    logger.info(f"Collection: {collection_name}")
    logger.info("Loading Collection Streams...")
    streams = api.list_collection_streams(collection_name)
    logger.info(f"Loaded: {streams}")
    # start data stream
    asyncio.get_event_loop().run_until_complete(begin_streaming_random_data(streams))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    try:
        main()
    except AssertionError as e:
        logger.error(f"Error: {e}")
