#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from serving import WebsocketClient


async def main():
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
    load_dotenv()

    server_host = "localhost"
    server_port = 3300

    client = WebsocketClient(server_host, server_port, backend="avro")
    await client.connect()

    collections = None
    collection_streams = None
    live_streams = None

    async def log_messages():

        nonlocal collections
        nonlocal collection_streams
        nonlocal live_streams

        while True:
            payload = await client.recvmsg()
            if payload is not None:
                topic, content = payload
                print(topic, content)
                if topic == client.protocol.LIST_COLLECTIONS:
                    collections = content["collections"]
                if topic == client.protocol.LIST_COLLECTION_STREAMS:
                    collection_streams = content["streams"]
                if topic == client.protocol.LIST_LIVE_STREAMS:
                    live_streams = content["streams"]
            else:
                print('payload=None')

    task = asyncio.create_task(log_messages())

    await client.sendmsg(*client.datamux.list_collections())
    await asyncio.sleep(2)
    assert collections

    await client.sendmsg(*client.datamux.list_collection_streams("adhd_sin"))
    await asyncio.sleep(2)
    assert collection_streams

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

    # await client.sendmsg(*client.datamux.replay_collection_stream(collection_name, stream_name, attrs))
    # await asyncio.sleep(10)

    await client.sendmsg(*client.datamux.restream_collection_stream(collection_name, stream_name, attrs))
    await asyncio.sleep(2)

    await client.sendmsg(*client.datamux.list_live_streams())
    await asyncio.sleep(2)
    assert live_streams
    live_stream = live_streams[0]

    ls_name = live_stream["name"]
    ls_attrs = live_stream["attrs"]
    await client.sendmsg(*client.datamux.relay_live_streams(ls_name, ls_attrs))
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
