#!/usr/bin/env python

import asyncio
import json
import threading
from typing import List

import numpy as np
import websockets
from pylsl import resolve_stream, StreamInfo, StreamInlet, LostError

SUBSCRIPTIONS = {}


async def server(websocket, path):
    while True:
        msg_in = await websocket.recv()
        request = json.loads(msg_in)
        await handleRequest(request, websocket)


def get_stream_info(x: StreamInfo):
    return {
        'id': x.source_id(),
        'channels': x.channel_count(),
        'name': x.name(),
        'type': x.type()
    }


async def handleRequest(request: dict, websocket: websockets.WebSocketServerProtocol):
    print(f"< {request}")
    command = request.get('command')
    response = {'command': command, 'error': None, 'data': None}
    if command == 'search':
        streams = resolve_stream()
        response['data'] = {'streams': [*map(lambda x: get_stream_info(x), streams)]}
    if command == 'subscribe':
        data: dict = request.get('data')
        source_id = data.get('id')
        source_name = data.get('name')
        source_type = data.get('type')
        # create stream inlets to pull data from
        streams: List[StreamInlet] = [StreamInlet(x) for x in resolve_stream('source_id', source_id) if x.name() == source_name and x.type() == source_type]
        # create async jobs to push data through the websocket
        thread = threading.Thread(target=create_streaming_task, args=(streams, websocket))
        # save references to stream inlets and thread
        if source_id in SUBSCRIPTIONS.keys():
            v: dict = SUBSCRIPTIONS[source_id]
            SUBSCRIPTIONS[source_id] = {'streams': [*v['streams'], *streams], 'threads': [*v['threads'], thread]}
        else:
            SUBSCRIPTIONS[source_id] = {'streams': streams, 'threads': [thread]}
        thread.start()
    print(f"> {response}")
    await ws_push(response, websocket)


async def ws_push(response: dict, websocket: websockets.WebSocketServerProtocol):
    msg_out = json.dumps(response)
    await websocket.send(msg_out)


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
    start_server = websockets.serve(server, "localhost", 8765)
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        print('started websocket server.')
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('stopped websockets server.\n')
