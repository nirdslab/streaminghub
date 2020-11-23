#!/usr/bin/env python

import asyncio
import json

import websockets
from pylsl import resolve_stream


async def hello(websocket, path):
    msg_in = await websocket.recv()
    request = json.loads(msg_in)

    print(f"< {request}")
    response = await handleRequest(request)
    print(f"> {response}")

    msg_out = json.dumps(response)
    await websocket.send(msg_out)


async def handleRequest(request: dict):
    if request.get('command') == 'search':
        streams = resolve_stream()
        return {'error': None, 'data': {'streams': [*map(lambda x: {'name': x.name(), 'type': x.type()}, streams)]}}
    response = {'error': None, 'data': {'status': 'OK'}}
    return response


if __name__ == '__main__':
    start_server = websockets.serve(hello, "localhost", 8765)
    try:
        print('starting websocket server...')
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('Interrupt received. Closing WebSockets Proxy...\n')
