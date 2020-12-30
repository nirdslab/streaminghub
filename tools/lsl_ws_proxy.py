#!/usr/bin/env python3

"""
A simple WebSocket proxy server for LSL.
This program discovers LSL services on a
local network and proxies them to other services
via WebSockets.
"""

import asyncio
import json
import logging
import os
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps, partial
from http import HTTPStatus
from typing import Tuple, Iterable, Optional, List

import websockets
import numpy as np
from pylsl import StreamInlet, resolve_stream, LostError
from websockets.http import Headers

from tools.util import stream_info_to_dict

logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()

ERROR_BAD_REQUEST = "Unknown Request"
EXECUTOR = ThreadPoolExecutor(max_workers=16)
RESPONSES = asyncio.Queue()


def run_async(func):
    @wraps(func)
    async def run(*args, **kwargs):
        return await loop.run_in_executor(EXECUTOR, partial(func, *args, **kwargs))

    return run


async def create_lsl_proxy(streams: List[StreamInlet]):
    keepalive = True
    while keepalive:
        try:
            for stream in streams:
                sample, timestamps = await run_async(stream.pull_chunk)(0.0)
                typ = stream.info().type()
                if len(sample) == 0:
                    continue
                await RESPONSES.put({'command': 'data', 'data': {'stream': typ, 'chunk': np.nan_to_num(sample, nan=-1).tolist()}})
        except LostError:
            keepalive = False
            logger.debug(f'LSL connection lost')
        except Exception:
            keepalive = False
            logger.debug(f'websocket connection lost')
            for stream in streams:
                await run_async(stream.close_stream)()
    else:
        logger.debug('streams unsubscribed')


async def consumer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
    async for message in websocket:
        logger.info(f'<: {message}')
        payload = json.loads(message)
        command = payload['command']
        response = {'command': command, 'error': None, 'data': None}

        # search command
        if command == 'search':
            streams = await run_async(resolve_stream)()
            response['data'] = {'streams': [*map(stream_info_to_dict, streams)]}
        # subscribe command
        elif command == 'subscribe':
            data: dict = payload['data']
            source_id, source_name, source_type = data['id'], data['name'], data['type']
            # get streams
            streams = await run_async(resolve_stream)(f"source_id='{source_id}' and name='{source_name}' and type='{source_type}'")
            # create stream inlets to pull data from
            stream_inlets: List[StreamInlet] = [StreamInlet(x, max_chunklen=1, recover=False) for x in streams]
            # create task to proxy LSL data into websockets
            loop.create_task(create_lsl_proxy(stream_inlets))
            response['data'] = {'status': 'started'}
        # unknown command
        else:
            response = {'command': None, 'error': ERROR_BAD_REQUEST, 'data': None}

        await RESPONSES.put(response)
        logger.debug(f'queued: {response}')


async def producer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
    while True:
        response = await RESPONSES.get()
        message = json.dumps(response)
        await websocket.send(message)
        logger.info(f'>: {message}')


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    consumer_task = asyncio.create_task(consumer_handler(websocket, path))
    producer_task = asyncio.create_task(producer_handler(websocket, path))
    done, pending = await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()


async def process_request(path: str, _: websockets.http.Headers) -> Optional[Tuple[HTTPStatus, Iterable[Tuple[str, str]], bytes]]:
    if path == '/ws':
        return None
    elif path == '/':
        return HTTPStatus(200), [], b''
    else:
        return HTTPStatus(404), [], b''


if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    start_server = websockets.serve(ws_handler, "0.0.0.0", port, process_request=process_request)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_server)
        logger.info(f'started websocket server on port={port}')
        loop.run_forever()
    except (KeyboardInterrupt, InterruptedError):
        logger.info('stopped websockets server.\n')
