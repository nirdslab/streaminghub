#!/usr/bin/env python3

"""
A simple WebSocket server for DataMux.
This program provides three modes of execution.

* **Proxy** mode: proxy live LSL data streams on the local network
* **Replay** mode: replay datasets from storage to mimic a live data stream
* **Simulate** mode: simulate random/guided data as a data stream

"""

import asyncio
import http
import logging
from typing import Optional, Tuple

from websockets.datastructures import Headers, HeadersLike
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol

from readers import CollectionReader, NodeReader
from serializers import Serializer

logger = logging.getLogger()
node_reader = NodeReader()
collection_reader = CollectionReader()
serializer = Serializer(backend="json")
res_queue = asyncio.Queue()

ERROR_BAD_REQUEST = "Unknown Request"
HTTPResponse = Tuple[http.HTTPStatus, HeadersLike, bytes]


async def producer_handler(
    websocket: WebSocketServerProtocol,
    _path: str,
):
    while websocket.open:
        topic, content = await res_queue.get()
        logger.debug(f"<: {topic}, {content}")
        message = serializer.encode(topic, content)
        await websocket.send(message)


async def consumer_handler(
    websocket: WebSocketServerProtocol,
    _path: str,
):
    while websocket.open:
        try:
            message = await websocket.recv()
        except ConnectionClosed:
            logger.info(f"client connection closed: {websocket.remote_address}")
            break
        assert isinstance(message, bytes)
        topic, content = serializer.decode(message)
        logger.debug(f"<: {topic}, {content}")
        await res_queue.put(process_cmd(topic, content))


async def ws_handler(
    websocket: WebSocketServerProtocol,
    path: str,
):
    logger.info(f"client connected: {websocket.remote_address}")
    producer_task = asyncio.create_task(producer_handler(websocket, path))
    consumer_task = asyncio.create_task(consumer_handler(websocket, path))
    done, pending = await asyncio.wait(
        [producer_task, consumer_task], return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    logger.info(f"client disconnected: {websocket.remote_address}")


async def process_request(
    path: str,
    headers: Headers,
) -> Optional[HTTPResponse]:
    if path == "/ws":
        return None
    elif path == "/":
        return http.HTTPStatus(200), [], b""
    else:
        return http.HTTPStatus(404), [], b""


def process_cmd(
    topic: bytes,
    content: dict,
) -> Tuple[bytes, dict]:
    # RELAY MODE (LSL) =========================================================================================================

    # list all lsl streams
    if topic == b"list_lsl_streams":
        node_reader.refresh_streams()
        streams = node_reader.list_streams()
        return topic, dict(streams=[s.dict() for s in streams])

    # relay data from a lsl stream
    elif topic == b"relay_lsl_stream":
        stream_name = content["stream_name"]
        task = node_reader.relay(stream_name, res_queue)
        status = 0 if task.cancelled() else 1
        return topic, dict(stream_name=stream_name, status=status)

    # REPLAY MODE (FILE) =======================================================================================================

    # list all collections
    elif topic == b"list_collections":
        collection_reader.refresh_collections()
        collections = collection_reader.list_collections()
        return topic, dict(collections=[c.dict() for c in collections])

    # list streams in a collection
    elif topic == b"list_collection_streams":
        collection_name = content["collection_name"]
        streams = collection_reader.list_streams(collection_name)
        return topic, dict(
            collection_name=collection_name, streams=[s.dict() for s in streams]
        )

    # replay data from a stream in a collection
    elif topic == b"replay_collection_stream":
        collection_name = content["collection_name"]
        stream_name = content["stream_name"]
        attrs = content["attrs"]
        task = collection_reader.replay(collection_name, stream_name, attrs, res_queue)
        status = 0 if task.cancelled() else 1
        return topic, dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
        )

    # RESTREAM MODE ======================================================================================================

    # restream data from a collection
    elif topic == b"restream_collection_stream":
        collection_name = content["collection_name"]
        stream_name = content["stream_name"]
        attrs = content["attrs"]
        task = collection_reader.restream(collection_name, stream_name, attrs)
        status = 0 if task.cancelled() else 1
        return topic, dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
        )

    # FALLBACK ===========================================================================================================
    else:
        return topic, dict(error=ERROR_BAD_REQUEST)
