#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from datamux import DataMuxClientAPI


async def main():
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
    load_dotenv()

    server_host = "localhost"
    server_port = 3300

    client = DataMuxClientAPI(rpc_backend="websocket", serialization_backend="avro")
    await client.connect(server_host, server_port)

    collections = await client.list_collections()
    print(collections)
    await asyncio.sleep(5)

    collection_streams = await client.list_collection_streams("adhd_sin")
    print(collection_streams)
    await asyncio.sleep(5)

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

    replay_hook = await client.replay_collection_stream(collection_name, stream_name, attrs)
    print(replay_hook)
    await asyncio.sleep(10)

    await client.restream_collection_stream(collection_name, stream_name, attrs)
    await asyncio.sleep(2)

    live_streams = await client.list_live_streams()
    await asyncio.sleep(2)

    assert live_streams
    live_stream = live_streams[0]
    ls_name = live_stream.name
    ls_attrs = live_stream.attrs

    relay_hook = await client.relay_live_streams(ls_name, ls_attrs)
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
