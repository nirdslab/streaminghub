#!/usr/bin/env python3

"""
A simple WebSocket proxy server for LSL.
This program discovers LSL services on a
local network and proxies them to other services
via WebSockets.
"""

import asyncio
import json
import os
import threading
from http import HTTPStatus
from typing import List, Callable, Union

import numpy as np
import websockets
from pylsl import resolve_stream, StreamInlet, LostError
from websockets.http import Headers
from websockets.server import HTTPResponse

from tools.util import stream_info_to_dict


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    async def callback(data):
        await ws_push(data, websocket)

    try:
        async for message in websocket:
            print(f"< {message}")
            await consumer(message, callback)
    except Exception:
        print('websocket handler closed')


async def consumer(message: str, callback: Callable):
    try:
        payload = json.loads(message)
        command = payload['command']
        response = {'command': command, 'error': None, 'data': None}

        if command == 'search':
            streams = resolve_stream()
            response['data'] = {'streams': [*map(stream_info_to_dict, streams)]}
        if command == 'subscribe':
            data: dict = payload['data']
            source_id, source_name, source_type = data['id'], data['name'], data['type']
            # create stream inlets to pull data from
            streams: List[StreamInlet] = [StreamInlet(x, max_chunklen=1, recover=False) for x in resolve_stream('source_id', source_id) if x.name() == source_name and x.type() == source_type]
            # create thread (with its own event loop) to proxy LSL data into websockets
            thread = threading.Thread(target=create_lsl_proxy, args=(streams, callback))
            thread.start()
    except:
        response = {'error': 'bad request'}
    await callback(response)


async def ws_push(payload: dict, websocket: websockets.WebSocketServerProtocol):
    message = json.dumps(payload)
    print(f"> {message}")
    await websocket.send(message)


def create_lsl_proxy(streams: List[StreamInlet], push: Callable):
    # create an event loop and begin data stream
    inner_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(inner_loop)
    inner_loop.run_until_complete(lsl_connector(streams, push))
    inner_loop.close()


async def lsl_connector(streams: List[StreamInlet], push: Callable):
    keepalive = True
    while keepalive:
        try:
            for stream in streams:
                sample, timestamps = stream.pull_chunk(0.0)
                typ = stream.info().type()
                if len(sample) == 0:
                    continue
                await push({'command': 'data', 'data': {'stream': typ, 'chunk': np.nan_to_num(sample, nan=-1).tolist()}})
        except LostError:
            keepalive = False
            print(f'LSL connection lost')
        except Exception:
            keepalive = False
            print(f'websocket connection lost')
            for stream in streams:
                stream.close_stream()
    else:
        print('streams unsubscribed')


async def process_request(path: str, request_headers: Headers) -> Union[HTTPResponse, None]:
    if path == '/ws':
        return None
    elif path == '/':
        return HTTPStatus(200), [], b''
    else:
        return HTTPStatus(404), [], b''


if __name__ == '__main__':
    port = int(os.getenv("PORT"))
    start_server = websockets.serve(ws_handler, "0.0.0.0", port, process_request=process_request)
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        print('started websocket server.')
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('stopped websockets server.\n')
