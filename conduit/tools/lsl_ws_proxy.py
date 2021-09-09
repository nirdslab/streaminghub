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
from typing import Tuple, Iterable, Optional, List, Dict, Any

import numpy as np
import websockets
from pylsl import StreamInlet, StreamInfo, resolve_stream, LostError

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


def pull_chunk(stream: StreamInlet, timeout: float):
  try:
    sample, timestamps = stream.pull_chunk(timeout)
    return sample, timestamps, None
  except Exception as e:
    logger.debug(f'LSL connection lost')
    return None, None, e


async def create_lsl_proxy(streams: List[StreamInlet]):
  keepalive = True
  while keepalive:
    try:
      for stream in streams:
        sample, timestamps, error = await run_async(pull_chunk)(stream, 0.0)
        if error:
          raise error
        typ = stream.info().type()
        if len(sample) == 0:
          continue
        await RESPONSES.put(
          {'command': 'data', 'data': {'stream': typ, 'chunk': np.nan_to_num(sample, nan=-1).tolist()}})
    except LostError:
      keepalive = False
  else:
    logger.debug('streams unsubscribed')


async def consumer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    try:
      message = await websocket.recv()
    except websockets.ConnectionClosed:
      logger.info(f'client connection closed: {websocket.remote_address}')
      break
    payload = json.loads(message)
    logger.debug(f'<: {json.dumps(payload)}')
    command = payload['command']
    response: Dict[str, Any] = {'command': command, 'error': None, 'data': None}

    # search command
    if command == 'search':
      streams = await run_async(resolve_stream)()
      response['data'] = {'streams': [*map(stream_info_to_dict, streams)]}
    # subscribe command
    elif command == 'subscribe':
      props = ['source_id', 'name', 'type']
      queries = [(d.get('id', None), d.get('name', None), d.get('type', None), d.get('attributes', None)) for d in
                 payload['data']]
      pred_str = ' and '.join(
        '(' + " or ".join([f"{props[i]}='{x}'" for x in set(c)]) + ')' for i, c in enumerate(list(zip(*queries))[:-1]))
      # run one query to get a superset of the requested streams
      result_streams: List[StreamInfo] = await run_async(resolve_stream)(pred_str)
      # filter streams by individual queries
      selected_streams: List[StreamInfo] = []
      for stream in result_streams:
        for (ds_id, ds_name, ds_type, ds_attributes) in queries:
          if stream.source_id() == ds_id and stream.name() == ds_name and stream.type() == ds_type:
            if not ds_attributes or len(ds_attributes) == 0:
              selected_streams.append(stream)
            else:
              # compare attributes and select only if all attributes match
              d: dict = stream_info_to_dict(stream).get("attributes", None)
              if d and all(d[k] == ds_attributes.get(k, None) for k in d):
                selected_streams.append(stream)
      logger.info("found %d streams matching the %d queries", len(selected_streams), len(queries))
      # create stream inlets to pull data from
      stream_inlets: List[StreamInlet] = [StreamInlet(x, max_chunklen=1, recover=False) for x in selected_streams]
      # create task to proxy LSL data into websockets
      loop.create_task(create_lsl_proxy(stream_inlets))
      response['data'] = {'status': 'started'}
    # unknown command
    else:
      response = {'command': None, 'error': ERROR_BAD_REQUEST, 'data': None}

    await RESPONSES.put(response)
    logger.debug(f'queued: {response}')


async def producer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    response = await RESPONSES.get()
    message = json.dumps(response)
    await websocket.send(message)
    logger.debug(f'>: {message}')


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
  logger.info(f'client connected: {websocket.remote_address}')
  consumer_task = asyncio.create_task(consumer_handler(websocket, path))
  producer_task = asyncio.create_task(producer_handler(websocket, path))
  done, pending = await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)
  for task in pending:
    task.cancel()
  logger.info(f'client disconnected: {websocket.remote_address}')


async def process_request(path: str, _: list) -> Optional[Tuple[HTTPStatus, Iterable[Tuple[str, str]], bytes]]:
  if path == '/ws':
    return None
  elif path == '/':
    return HTTPStatus(200), [], b''
  else:
    return HTTPStatus(404), [], b''


if __name__ == '__main__':
  default_port = os.getenv("PORT")
  port = int(default_port)
  start_server = websockets.serve(ws_handler, "0.0.0.0", port, process_request=process_request)
  loop = asyncio.get_event_loop()
  try:
    loop.run_until_complete(start_server)
    logger.info(f'started websocket server on port={port}')
    loop.run_forever()
  except (KeyboardInterrupt, InterruptedError):
    logger.info('interrupt received. stopped websockets server.\n')
