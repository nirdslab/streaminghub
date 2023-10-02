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
import threading

from dfds.typing import Stream
from rich.logging import RichHandler

import util
from api import DataMuxAPI

DIGIT_CHARS = "0123456789"
SHUTDOWN_FLAG = threading.Event()
logger = logging.getLogger(__name__)

api = DataMuxAPI()


async def log_sink(sink: asyncio.Queue, max_items: int = 100):
    for _ in range(max_items):
        value = await sink.get()
        logging.info(value)


async def begin_streaming(collection_name: str, streams: list[Stream]):
    # state variables
    loop = asyncio.get_event_loop()
    tasks = []

    logger.info(f"Started data streaming")

    for stream in streams:
        node = stream.node
        assert node is not None
        device = node.device
        assert device is not None

        for stream in streams:
            source_id = util.gen_randseq()
            logger.info(f"Source [{source_id}]: {device.model}, {device.manufacturer} ({device.category})")

            sink = asyncio.Queue()
            api.replay_collection_stream(collection_name, stream.name, stream.attrs, sink)

            tasks.append(loop.create_task(log_sink(sink)))
            logger.info(f"Source [{source_id}]: started")

    await asyncio.gather(*tasks)
    logger.info(f"Ended data streaming")


def main():
    # get default args
    # create parser and parse args
    parser = argparse.ArgumentParser(prog="replay.py")
    # required args
    parser.add_argument("--collection-name", "-n", required=True)
    # optional args
    parser.add_argument("--attributes", "-a", required=False)
    parser.add_argument("--data-dir", "-d", required=False, default=os.getenv("SH_DATA_DIR"))
    parser.add_argument("--meta-dir", "-m", required=False, default=os.getenv("SH_META_DIR"))
    # parse all args
    known_args, args = parser.parse_known_args()
    collection_name = known_args.collection_name
    # print args
    logger.info(f"Collection Name: {collection_name}")
    logger.info(f"Data Directory: {known_args.data_dir}")
    logger.info(f"Meta Directory: {known_args.meta_dir}")
    # get dataset spec
    streams = api.list_collection_streams(collection_name)
    # get data sources
    assert len(streams) > 0, f"Dataset does not have data sources"
    # spawn a worker thread for streaming
    logger.info("=== Begin streaming ===")
    try:
        asyncio.run(begin_streaming(collection_name, streams))
    except (KeyboardInterrupt, InterruptedError):
        logger.info("Interrupt received. Ending all stream tasks..")
    logger.info("All streaming tasks ended")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
    try:
        main()
    except AssertionError as e:
        logger.error(f"Error: {e}")
