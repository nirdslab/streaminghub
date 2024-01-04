#!/usr/bin/env python3

import asyncio
import logging
import timeit

from rich.logging import RichHandler

import datamux.util as util
from datamux.remote.api import DataMuxRemoteAPI


async def main():
    N = 10
    P = 8000
    t_replay = []
    t_relay = []
    server_host = "localhost"
    server_port = 3300

    api = DataMuxRemoteAPI(rpc_name="websocket", codec_name="avro")
    await api.connect(server_host, server_port)

    for _ in range(N):
        # test 1 - collections
        logger.info("listing collections")
        collections = await api.list_collections()
        logger.info(f"received collections: {collections}")

        # test 2 - collection streams
        logger.info("listing collection streams - tdbrain")
        collection_streams = await api.list_collection_streams("tdbrain")
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
        sink = asyncio.Queue()
        ack = await api.replay_collection_stream(collection_name, stream_name, attrs, sink)
        assert ack.randseq is not None
        logger.info(f"received ack for collection stream: {ack}")
        # print P points or until EOF
        startTime = timeit.default_timer()
        for i in range(P):
            item = await sink.get()
            logger.info(item)
            if item == util.END_OF_STREAM:
                break
            if i == 0:
                startTime = timeit.default_timer()
        endTime = timeit.default_timer()
        t_replay.append(endTime - startTime)
        await api.stop_task(ack.randseq)

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
        assert ack.randseq is not None
        logger.info(f"received ack for live stream: {ack}")
        # print P points or until EOF
        startTime = timeit.default_timer()
        for i in range(P):
            item = await sink.get()
            logger.info(item)
            if item == util.END_OF_STREAM:
                break
            if i == 0:
                startTime = timeit.default_timer()
        endTime = timeit.default_timer()
        t_replay.append(endTime - startTime)
        await api.stop_task(ack.randseq)

    print("Elapsed Time (Replay): ", t_replay)
    print("Elapsed Time (Relay): ", t_relay)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
