#!/usr/bin/env python

import asyncio
import json
import threading
from typing import List

import numpy as np
import websockets
from pylsl import resolve_stream, StreamInlet, LostError

from tools.util import stream_info_to_dict


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    async for message in websocket:
        print(f"< {message}")
        await consumer(message, websocket)


async def consumer(message: str, websocket: websockets.WebSocketServerProtocol):
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
        # create async jobs to push data through the websocket
        thread = threading.Thread(target=create_streaming_task, args=(streams, websocket))
        thread.start()
    await ws_push(response, websocket)


async def ws_push(payload: dict, websocket: websockets.WebSocketServerProtocol):
    message = json.dumps(payload)
    print(f"> {message}")
    await websocket.send(message)


def create_streaming_task(streams: List[StreamInlet], websocket: websockets.WebSocketServerProtocol):
    # create an event loop and begin data stream
    inner_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(inner_loop)
    inner_loop.run_until_complete(proxy_stream(streams, websocket))
    inner_loop.close()


async def proxy_stream(streams: List[StreamInlet], websocket: websockets.WebSocketServerProtocol):
    thread = threading.current_thread()
    thread.alive = True
    while thread.alive:
        for stream in streams:
            try:
                sample, timestamps = stream.pull_chunk(0.0)
                typ = stream.info().type()
                if len(sample) == 0:
                    continue
                await ws_push({'command': 'data', 'data': {'stream': typ, 'chunk': np.nan_to_num(sample, nan=-1).tolist()}}, websocket)
            except LostError:
                thread.alive = False
                break
    if not thread.alive:
        print('stream unsubscribed')


if __name__ == '__main__':
    start_server = websockets.serve(ws_handler, "localhost", 8765)
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        print('started websocket server.')
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('stopped websockets server.\n')
