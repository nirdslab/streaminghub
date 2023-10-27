#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

import util
from remote.api import DataMuxRemoteAPI


async def main():
    server_host = "localhost"
    server_port = 3300

    api = DataMuxRemoteAPI(rpc_name="websocket", codec_name="avro")
    await api.connect(server_host, server_port)

    # test 1 - collections
    logger.info("listing collections")
    collections = await api.list_collections()
    logger.info(f"received collections: {collections}")

    # test 2 - collection streams
    logger.info("listing collection streams - adhd_sin")
    collection_streams = await api.list_collection_streams("adhd_sin")
    logger.info(f"received collection_streams: {collection_streams}")

    # test 3 - replay collection stream
    logger.info("replaying collection stream")
    collection_name = "adhd_sin"
    stream_name = "Gaze"
    attrs = dict(
        {
            "noise": "0",
            "participant": "12",
            "question": "10",
        }
    )
    sink = asyncio.Queue()
    ack = await api.replay_collection_stream(collection_name, stream_name, attrs, sink)
    logger.info(f"received ack for collection stream: {ack}")
    # print 1000 points or until EOF
    for _ in range(1000):
        item = await sink.get()
        logger.info(item)
        if item == util.END_OF_STREAM:
            break

    # test 4 - make LSL stream from a collection stream
    logger.info("creating LSL stream")
    status = await api.publish_collection_stream(collection_name, stream_name, attrs)
    logger.info(f"created LSL stream: {status}")
    assert status
    await asyncio.sleep(5)

    # test 5 - list all LSL streams
    logger.info("listing LSL streams")
    live_streams = await api.list_live_streams()
    logger.info(f"got LSL streams: {live_streams}")

    # test 6 - relay LSL stream
    logger.info("relaying LSL stream")
    assert len(live_streams) > 0
    ls = live_streams[0]
    sink = asyncio.Queue()
    ack = await api.read_live_stream(ls.name, ls.attrs, sink)
    logger.info(f"received ack for live stream: {ack}")
    # print 1000 points or until EOF
    for _ in range(1000):
        item = await sink.get()
        logger.info(item)
        if item == util.END_OF_STREAM:
            break


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    load_dotenv()
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
