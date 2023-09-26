#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from remote_api import DataMuxRemoteAPI


async def main():
    server_host = "localhost"
    server_port = 3300

    api = DataMuxRemoteAPI(rpc_backend="websocket", serialization_backend="avro")
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
            "diagnosis": "Non-ADHD",
            "gender": "female",
            "noise": "0",
            "participant": "12",
            "question": "10",
            "collection": "adhd_sin",
            "id": "gaze",
        }
    )
    replay_hook = await api.replay_collection_stream(collection_name, stream_name, attrs)
    logger.info("received replay hook for collection stream")
    # print 100 points
    for _ in range(100):
        item = await replay_hook.get()
        logger.info(item)

    # # test 4 - make LSL stream from a collection stream
    # logger.info("creating LSL stream")
    # await api.restream_collection_stream(collection_name, stream_name, attrs)
    # logger.info("created LSL stream")

    # # test 5 - list all LSL streams
    # logger.info("listing LSL streams")
    # live_streams = await api.list_live_streams()
    # logger.info(f"got LSL streams: {live_streams}")

    # # test 6 - relay LSL stream
    # logger.info("relaying LSL stream")
    # assert len(live_streams) > 0
    # ls = live_streams[0]
    # relay_hook = await api.relay_live_streams(ls.name, ls.attrs)
    # logger.info("received relay hook for LSL stream")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    logger = logging.getLogger(__name__)
    asyncio.run(main())
