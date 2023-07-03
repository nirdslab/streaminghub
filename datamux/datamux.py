#!/usr/bin/env python3

"""
A simple WebSocket server for DataMux.
This program provides three modes of execution.

* **Proxy** mode: proxy live LSL data streams on the local network
* **Replay** mode: replay datasets from storage to mimic a live data stream
* **Simulate** mode: simulate random/guided data as a data stream

"""

import asyncio
import json
import logging
import os
import http
from typing import Tuple, Optional

from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve
from websockets.datastructures import Headers, HeadersLike

from readers import NodeReader, CollectionReader
from serializers import Serializer

logger = logging.getLogger()
node_reader = NodeReader()
collection_reader = CollectionReader()
serializer = Serializer(backend="json")

ERROR_BAD_REQUEST = "Unknown Request"
HTTPResponse = Tuple[http.HTTPStatus, HeadersLike, bytes]


async def producer_handler(
    websocket: WebSocketServerProtocol,
    _path: str,
):
    while websocket.open:
        response = await res_queue.get()
        message = serializer.encode(**response)
        await websocket.send(message)
        # logger.debug(f'>: {message}')


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
        payload = json.loads(message)
        # logger.debug(f'<: {json.dumps(payload)}')
        await res_queue.put(process_cmd(payload))


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
    payload: dict,
) -> dict:
    command = payload["command"]

    # RELAY MODE (LSL) =========================================================================================================

    # list all lsl streams
    if command == "list_lsl_streams":
        streams = node_reader.list_streams()
        return dict(
            topic=command,
            streams=streams,
        )

    # relay data from a lsl stream
    elif command == "relay_lsl_stream":
        stream_name = payload["data"]["stream_name"]
        task = node_reader.relay(stream_name, res_queue)
        status = 0 if task.cancelled() else 1
        return dict(
            topic=command,
            stream_name=stream_name,
            status=status,
        )

    # REPLAY MODE (FILE) =======================================================================================================

    # list all collections
    elif command == "list_collections":
        collections = collection_reader.get_collections()
        return dict(
            topic=command,
            collections=collections,
        )

    # list streams in a collection
    elif command == "list_collection_streams":
        collection_name = payload["data"]["collection_name"]
        streams = collection_reader.list_streams(collection_name)
        return dict(
            topic=command,
            collection_name=collection_name,
            streams=streams,
        )

    # replay data from a stream in a collection
    elif command == "replay_collection_stream":
        collection_name = payload["data"]["collection_name"]
        stream_name = payload["data"]["stream_name"]
        task = collection_reader.replay(collection_name, stream_name, res_queue)
        status = 0 if task.cancelled() else 1
        return dict(
            topic=command,
            collection_name=collection_name,
            stream_name=stream_name,
            status=status,
        )

    # RESTREAM MODE ======================================================================================================

    # restream data from a collection
    elif command == "restream_collection_stream":
        collection_name = payload["data"]["collection_name"]
        stream_name = payload["data"]["stream_name"]
        task = collection_reader.restream(collection_name, stream_name)
        status = 0 if task.cancelled() else 1
        return dict(
            topic=command,
            collection_name=collection_name,
            stream_name=stream_name,
            status=status,
        )

    # FALLBACK ===========================================================================================================
    else:
        return dict(
            topic=command,
            error=ERROR_BAD_REQUEST,
        )


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
    default_port = os.getenv("DATAMUX_PORT", "3300")
    port = int(default_port)
    start_server = serve(ws_handler, "0.0.0.0", port, process_request=process_request)
    main_loop = asyncio.get_event_loop()
    res_queue = asyncio.Queue()
    try:
        main_loop.run_until_complete(start_server)
        logger.info(f"started datamux on port={port}")
        main_loop.run_forever()
    except (KeyboardInterrupt, InterruptedError):
        logger.info("interrupt received. stopped datamux.\n")
