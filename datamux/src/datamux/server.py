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
from pathlib import Path
from typing import Tuple, Iterable, Optional, List, Dict, Any, Generator

import websockets
from pylsl import StreamInlet, StreamInfo, resolve_streams, resolve_bypred

import dfs
from datamux.util import map_lsl_stream_info_to_dict, proxy_lsl_stream, dataset_attrs_and_data, replay_data

logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()

ERROR_BAD_REQUEST = "Unknown Request"
RESPONSES = asyncio.Queue()


async def consumer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    try:
      message = await websocket.recv()
    except websockets.ConnectionClosed:
      logger.info(f'client connection closed: {websocket.remote_address}')
      break
    payload = json.loads(message)
    logger.info(f'<: {json.dumps(payload)}')
    # consume payload, and generate response
    response = await consume(payload)

    await RESPONSES.put(response)
    logger.info(f'queued: {response}')


def proxy_mode_get_live_streams(response: Dict[str, Any]):
  live_streams = resolve_streams()
  response['command'] = 'live_streams'
  response['data'] = {'streams': [*map(map_lsl_stream_info_to_dict, live_streams)]}


def proxy_mode_sub_live_streams(data: List[Dict], response: Dict[str, Any]):
  props = ['source_id', 'name', 'type']
  queries = [(d.get('id', None), d.get('name', None), d.get('type', None), d.get('attributes', None)) for d in data]
  pred_str = ' and '.join(
    '(' + " or ".join([f"{props[i]}='{x}'" for x in set(c)]) + ')' for i, c in enumerate(list(zip(*queries))[:-1]))
  # run one query to get a superset of the requested streams
  result_streams: List[StreamInfo] = resolve_bypred(pred_str)
  # filter streams by individual queries
  selected_streams: List[StreamInfo] = []
  for stream in result_streams:
    for (ds_id, ds_name, ds_type, ds_attributes) in queries:
      if stream.source_id() == ds_id and stream.name() == ds_name and stream.type() == ds_type:
        if not ds_attributes or len(ds_attributes) == 0:
          selected_streams.append(stream)
        else:
          # compare attributes and select only if all attributes match
          d: dict = map_lsl_stream_info_to_dict(stream).get("attributes", None)
          if d and all(d[k] == ds_attributes.get(k, None) for k in d):
            selected_streams.append(stream)
  logger.info("found %d streams matching the %d queries", len(selected_streams), len(queries))
  # create tasks to proxy selected streams
  for x in selected_streams:
    # create stream inlet for selected stream
    stream_inlet = StreamInlet(x, max_chunklen=1, recover=False)
    loop.create_task(proxy_lsl_stream(stream_inlet, RESPONSES))
  response['command'] = 'live_streams'
  response['data'] = {'status': 'started'}


def replay_mode_get_datasets(response: Dict[str, Any]):
  dataset_names = [*map(lambda x: x[:-5], Path(dfs.get_dataset_dir()).glob("*.json"))]
  dataset_specs: List[dfs.DataSetSpec] = [*map(dfs.get_dataset_spec, dataset_names)]
  response['command'] = 'datasets'
  response['data'] = {'datasets': dataset_specs}


def replay_mode_get_repl_streams(dataset_name: str, response: Dict[str, Any]):
  dataset_spec = dfs.get_dataset_spec(dataset_name)
  attrs_and_streams = []
  for attrs, data_stream in dataset_attrs_and_data(dataset_spec, dataset_name):
    sources = dataset_spec.sources
    for source_id in sources:
      source = sources[source_id]
      streams = source.streams
      for stream_id in streams:
        stream = streams[stream_id]
        attrs_and_streams.append({**attrs, 'stream': stream, 'device': source.device})
  response['command'] = 'repl_streams'
  response['data'] = {'streams': attrs_and_streams}


def replay_mode_sub_repl_streams(data: List[Dict], response: Dict[str, Any]):
  # TODO update this to replay without LSL
  queries = [(d.get('id', None), d.get('name', None), d.get('type', None), d.get('attributes', None)) for d in data]
  # list of selected streams
  selected_streams: List[Tuple[Dict[str, Any], Generator[Dict[str, float], None, None]]] = []
  # populate list of selected streams by iterating each dataset and filtering streams by attributes
  for (ds_id, ds_name, ds_type, ds_attributes) in queries:
    dataset_spec = dfs.get_dataset_spec(ds_name)
    for attrs_and_data in dataset_attrs_and_data(dataset_spec, ds_name):
      attrs, data_stream = attrs_and_data
      # compare attributes and select only if all attributes match
      if attrs and all(attrs[k] == ds_attributes.get(k, None) for k in attrs):
        selected_streams.append(attrs_and_data)
  logger.info("matched %d streams for the %d queries", len(selected_streams), len(queries))
  # create tasks to replay selected streams
  for attrs, data_stream in selected_streams:
    # create task to replay data
    loop.create_task(replay_data(attrs, data_stream, RESPONSES))
  response['command'] = 'repl_streams'
  response['data'] = {'status': 'started'}


async def consume(payload: Any):
  command = payload['command']
  response: Dict[str, Any] = {'command': None, 'error': None, 'data': None}
  # ====================================================================================================================
  # PROXY MODE
  # ====================================================================================================================
  if command == 'get_live_streams':
    proxy_mode_get_live_streams(response)
  elif command == 'sub_live_streams':
    proxy_mode_sub_live_streams(payload['data'], response)
  # ====================================================================================================================
  # REPLAY MODE
  # ====================================================================================================================
  elif command == 'get_datasets':
    replay_mode_get_datasets(response)
  elif command == 'get_repl_streams':
    replay_mode_get_repl_streams(payload['data']['dataset_name'], response)
  elif command == 'sub_repl_streams':
    replay_mode_sub_repl_streams(payload['data'], response)
  # ====================================================================================================================
  # SIMULATE MODE
  # ====================================================================================================================
  # TODO implement this
  # unknown command
  else:
    response = {'command': None, 'error': ERROR_BAD_REQUEST, 'data': None}
  return response


async def producer_handler(websocket: websockets.WebSocketServerProtocol, _path: str):
  while websocket.open:
    response = await RESPONSES.get()
    message = json.dumps(response)
    await websocket.send(message)
    logger.info(f'>: {message}')


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
  default_port = os.getenv("STREAMINGHUB_PORT")
  port = int(default_port)
  start_server = websockets.serve(ws_handler, "0.0.0.0", port, process_request=process_request)
  loop = asyncio.get_event_loop()
  try:
    loop.run_until_complete(start_server)
    logger.info(f'started websocket server on port={port}')
    loop.run_forever()
  except (KeyboardInterrupt, InterruptedError):
    logger.info('interrupt received. stopped websockets server.\n')
