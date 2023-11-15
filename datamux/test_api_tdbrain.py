#!/usr/bin/env python3

import asyncio
import logging
import multiprocessing

import timeit

from dotenv import load_dotenv
from rich.logging import RichHandler

import util
from api import DataMuxAPI


async def main():
    times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    for i in range (10):
        api = DataMuxAPI()

        # test 1 - collections
        logger.info("listing collections")
        collections = api.list_collections()
        logger.info(f"received collections: {collections}")

        # test 2 - collection streams
        logger.info("listing collection streams - tdbrain")
        collection_streams = api.list_collection_streams("tdbrain")
        logger.info(f"received collection_streams: {collection_streams}")

        # test 3 - replay collection stream
        logger.info("replaying collection stream")
        collection_name = "tdbrain"
        stream_name = "eeg"
        attrs = dict(
            {
                "subject": "19681349",
                "session": "1",
                "task": "restEC",
            }
        )
        sink = multiprocessing.Queue()
        ack = api.replay_collection_stream(collection_name, stream_name, attrs, sink)
        assert ack.randseq is not None
        logger.info(f"received ack for collection stream: {ack}")
        # print 1000 points or until EOF
        for _ in range(8000):
            item = sink.get()
            logger.info(item)
            if item == util.END_OF_STREAM:
                break
            if _ == 0:
                startTime = timeit.default_timer()
        api.stop_task(ack.randseq)

        endTime = timeit.default_timer()
        # test 4 - make LSL stream from a collection stream
        logger.info("creating LSL stream")
        status = api.publish_collection_stream(collection_name, stream_name, attrs)
        logger.info(f"created LSL stream: {status}")
        assert status
        await asyncio.sleep(5)

        # test 5 - list all LSL streams
        logger.info("listing LSL streams")
        live_streams = api.list_live_streams()
        logger.info(f"got LSL streams: {live_streams}")

        # test 6 - relay LSL stream
        logger.info("relaying LSL stream")
        assert len(live_streams) > 0
        ls = live_streams[0]
        sink = multiprocessing.Queue()
        ack = api.read_live_stream(ls.name, ls.attrs, sink)
        assert ack.randseq is not None
        logger.info(f"received ack for live stream: {ack}")
        # print 1000 points or until EOF
        for _ in range(1000):
            item = sink.get()
            logger.info(item)
            if item == util.END_OF_STREAM:
                break
        api.stop_task(ack.randseq)

        times[i] = [endTime - startTime]

    for x in range(10):
        print("Elapsed Time: ", times[x])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    load_dotenv()
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")