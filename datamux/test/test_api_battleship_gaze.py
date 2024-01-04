#!/usr/bin/env python3

import asyncio
import logging
import multiprocessing

import datamux.util as util
from datamux.api import DataMuxAPI
from rich.logging import RichHandler


async def main():
    N = 10
    P = 8000
    api = DataMuxAPI()

    # test 1 - collections
    logger.info("listing collections")
    collections = api.list_collections()
    logger.info(f"received collections: {collections}")

    # test 2 - collection streams
    logger.info("listing collection streams - battleship_gaze")
    collection_streams = api.list_collection_streams("battleship_gaze")
    logger.info(f"received collection_streams: {collection_streams}")

    # test 3 - replay collection stream
    logger.info("replaying collection stream")
    collection_name = "battleship_gaze"
    stream_name = "Gaze"
    attrs = dict(
        {
            "session": "1",
            "stream_name": "gaze",
        }
    )
    sink = multiprocessing.Queue()
    ack = api.replay_collection_stream(collection_name, stream_name, attrs, sink)
    assert ack.randseq is not None
    logger.info(f"received ack for collection stream: {ack}")
    # print P points or until EOF
    for _ in range(P):
        item = sink.get()
        logger.info(item)
        if item == util.END_OF_STREAM:
            break
    ack = api.stop_task(ack.randseq)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
