#!/usr/bin/env python3

"""
A simple WebSocket proxy server for LSL.
This program discovers LSL services on a
local network and proxies them to other services
via WebSockets.
"""

import asyncio
import json
import threading
from typing import List, Callable

import numpy as np
import websockets
from pylsl import resolve_stream, StreamInlet, LostError

from tools.util import stream_info_to_dict


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    async def callback(data):
        await ws_push(data, websocket)

    async for message in websocket:
        print(f"< {message}")
        await consumer(message, callback)


async def consumer(message: str, callback: Callable):
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
    else:
        print('stream unsubscribed')


if __name__ == '__main__':
    start_server = websockets.serve(ws_handler, "0.0.0.0", 8765)
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        print('started websocket server.')
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('stopped websockets server.\n')
