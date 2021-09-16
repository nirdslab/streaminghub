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
from http import HTTPStatus
from typing import Tuple, Iterable, Optional, Any

import websockets

from datamux.relay_mode import RelayMode
from datamux.replay_mode import ReplayMode

logger = logging.getLogger()

ERROR_BAD_REQUEST = "Unknown Request"


async def producer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    response = await res_queue.get()
    message = json.dumps(response)
    await websocket.send(message)
    # logger.debug(f'>: {message}')


async def consumer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    try:
      message = await websocket.recv()
    except websockets.ConnectionClosed:
      logger.info(f'client connection closed: {websocket.remote_address}')
      break
    payload = json.loads(message)
    # logger.debug(f'<: {json.dumps(payload)}')
    await res_queue.put(process_cmd(payload))


async def ws_handler(websocket: websockets.WebSocketServerProtocol, path: str):
  logger.info(f'client connected: {websocket.remote_address}')
  producer_task = asyncio.create_task(producer_handler(websocket, path))
  consumer_task = asyncio.create_task(consumer_handler(websocket, path))
  done, pending = await asyncio.wait([producer_task, consumer_task], return_when=asyncio.FIRST_COMPLETED)
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


def process_cmd(payload: Any):
  command = payload['command']
  # RELAY MODE =========================================================================================================
  if command == 'get_live_streams':
    return RelayMode.get_live_streams()
  elif command == 'sub_live_streams':
    return RelayMode.sub_live_streams(payload['data'], res_queue)
  # REPLAY MODE ========================================================================================================
  elif command == 'get_datasets':
    return ReplayMode.get_datasets()
  elif command == 'get_repl_streams':
    return ReplayMode.get_repl_streams(payload['data']['dataset_name'])
  elif command == 'sub_repl_streams':
    return ReplayMode.sub_repl_streams(payload['data'], res_queue)
  # SIMULATE MODE ======================================================================================================
  # TODO implement simulate mode functions
  # FALLBACK ===========================================================================================================
  else:
    return {'command': 'error_notification', 'error': ERROR_BAD_REQUEST, 'data': None}


if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.DEBUG)
  default_port = os.getenv("STREAMINGHUB_PORT")
  port = int(default_port)
  start_server = websockets.serve(ws_handler, "0.0.0.0", port, process_request=process_request)
  main_loop = asyncio.get_event_loop()
  res_queue = asyncio.Queue()
  try:
    main_loop.run_until_complete(start_server)
    logger.info(f'started websocket server on port={port}')
    main_loop.run_forever()
  except (KeyboardInterrupt, InterruptedError):
    logger.info('interrupt received. stopped websockets server.\n')
