#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from remote_api import DataMuxRemoteAPI


async def main():
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()

    server_host = "localhost"
    server_port = 3300

    api = DataMuxRemoteAPI(rpc_backend="websocket", serialization_backend="avro")
    await api.connect(server_host, server_port)

    # test 1 - collections
    print("listing collections")
    collections = await api.list_collections()
    print(f"received collections: {collections}")
    await asyncio.sleep(5)

    # test 2 - collection streams
    print("listing collection streams - adhd_sin")
    collection_streams = await api.list_collection_streams("adhd_sin")
    print(f"received collection_streams: {collection_streams}")
    await asyncio.sleep(5)

    # test 3 - replay collection stream
    print("replaying collection stream")
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
    print("received replay hook for collection stream")
    print(replay_hook)
    await asyncio.sleep(10)

    # test 4 - make LSL stream from a collection stream
    print("creating LSL stream")
    await api.restream_collection_stream(collection_name, stream_name, attrs)
    print("created LSL stream")
    await asyncio.sleep(2)

    # test 5 - list all LSL streams
    print("listing LSL streams")
    live_streams = await api.list_live_streams()
    print(f"got LSL streams: {live_streams}")
    await asyncio.sleep(2)

    # test 6 - relay LSL stream
    print("relaying LSL stream")
    assert len(live_streams) > 0
    ls = live_streams[0]
    relay_hook = await api.relay_live_streams(ls.name, ls.attrs)
    print("received relay hook for LSL stream")
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
