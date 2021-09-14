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
from typing import Tuple, Iterable, Optional, List, Dict, Any, Union

import websockets
from pylsl import StreamInfo as LiveStreamInfo
from pylsl import StreamInlet as LiveStreamInlet
from pylsl import resolve_bypred as resolve_live_streams_by_pred_str
from pylsl import resolve_streams as resolve_all_live_streams

import dfs
from datamux.util import map_live_stream_info_to_dict, start_live_stream, find_repl_streams, \
  start_repl_stream, DICT_GENERATOR, DICT

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


class ProxyMode:

  @staticmethod
  def get_live_streams():
    live_streams = resolve_all_live_streams()
    return {
      'command': 'live_streams',
      'data': {'streams': [*map(map_live_stream_info_to_dict, live_streams)]},
      'error': None
    }

  @staticmethod
  def sub_live_streams(data: List[Dict[str, Union[str, dict]]]):
    # source = <source_id> | type = <stream_id>
    stream_query = [(
      str(d.get('source', '')),
      str(d.get('type', '')),
      dict(d.get('attributes', {}))
    ) for d in data]
    props = ['source_id', 'type']
    pred_str = ' and '.join(
      '(' + " or ".join(
        [f"{props[i]}='{x}'" for x in set(c)]
      ) + ')' for i, c in enumerate(list(zip(*stream_query))[:-1])
    )
    # run one query to get a superset of the requested streams
    available_live_stream_info: List[LiveStreamInfo] = resolve_live_streams_by_pred_str(pred_str)
    # filter streams by individual queries
    selected_live_stream_info: List[LiveStreamInfo] = []
    for live_stream_info in available_live_stream_info:
      for (sq_source, sq_type, sq_attrs) in stream_query:
        if live_stream_info.source_id() == sq_source and live_stream_info.type() == sq_type:
          if not sq_attrs or len(sq_attrs) == 0:
            selected_live_stream_info.append(live_stream_info)
          else:
            # compare attributes and select only if all attributes match
            sq_attrs: dict = map_live_stream_info_to_dict(live_stream_info).get("attributes", None)
            if sq_attrs and all(sq_attrs[k] == sq_attrs.get(k, None) for k in sq_attrs):
              selected_live_stream_info.append(live_stream_info)
    logger.info("found %d streams matching the %d queries", len(selected_live_stream_info), len(stream_query))
    # create tasks to proxy selected streams
    for live_stream_info in selected_live_stream_info:
      # create stream inlet for selected stream
      loop.create_task(start_live_stream(
        LiveStreamInlet(live_stream_info, max_chunklen=1, recover=False),
        RESPONSES
      ))
    return {
      'command': 'notification',
      'data': {'message': f'started {len(selected_live_stream_info)} live streams'},
      'error': None
    }


class ReplayMode:

  @staticmethod
  def get_datasets():
    dataset_names = [*map(lambda x: x[:-5], Path(dfs.get_dataset_dir()).glob("*.json"))]
    dataset_specs: List[dfs.DataSetSpec] = [*map(dfs.get_dataset_spec, dataset_names)]
    return {
      'command': 'datasets',
      'data': {'datasets': dataset_specs},
      'error': None
    }

  @staticmethod
  def get_repl_streams(dataset_name: str):
    dataset_spec = dfs.get_dataset_spec(dataset_name)
    repl_stream_info: List[Dict[str, Union[str, dict]]] = []
    for repl_stream, s_attrs in find_repl_streams(dataset_spec):
      sources = dataset_spec.sources
      for source_id in sources:
        source = sources[source_id]
        streams = source.streams
        for stream_id in streams:
          stream = streams[stream_id]
          repl_stream_info.append({**s_attrs, 'stream': stream, 'device': source.device})
    return {
      'command': 'repl_streams',
      'data': {'streams': repl_stream_info},
      'error': None
    }

  @staticmethod
  def sub_repl_streams(data: List[Dict[str, Union[str, dict]]]):
    # dataset = <dataset_id> | source = <source_id> | type = <stream_id>
    stream_query = [(
      str(d.get('dataset', '')),
      str(d.get('source', '')),
      str(d.get('type', '')),
      dict(d.get('attributes', {}))
    ) for d in data]
    # list of selected streams
    selected_repl_streams: List[Tuple[DICT_GENERATOR, str, str, DICT]] = []
    # populate list of selected streams by iterating each dataset and filtering streams by attributes
    for sq_dataset, sq_source, sq_type, sq_attrs in stream_query:
      dataset_spec = dfs.get_dataset_spec(sq_dataset)
      for repl_stream, s_attrs in find_repl_streams(dataset_spec, **sq_attrs):
        # add source and type information to attrs, for filtering
        selected_repl_streams.append((repl_stream, sq_source, sq_type, s_attrs))
    logger.info("matched %d streams for the %d queries", len(selected_repl_streams), len(stream_query))
    # create tasks to replay selected streams
    for repl_stream, s_source, s_type, s_attrs in selected_repl_streams:
      # create task to replay data
      loop.create_task(start_repl_stream(repl_stream, s_source, s_type, s_attrs, RESPONSES))
    return {
      'command': 'notification',
      'data': {'message': f'started {len(selected_repl_streams)} repl streams'},
      'error': None
    }


async def consume(payload: Any):
  command = payload['command']
  # ====================================================================================================================
  # PROXY MODE
  # ====================================================================================================================
  if command == 'get_live_streams':
    ProxyMode.get_live_streams()
  elif command == 'sub_live_streams':
    ProxyMode.sub_live_streams(payload['data'])
  # ====================================================================================================================
  # REPLAY MODE
  # ====================================================================================================================
  elif command == 'get_datasets':
    ReplayMode.get_datasets()
  elif command == 'get_repl_streams':
    ReplayMode.get_repl_streams(payload['data']['dataset_name'])
  elif command == 'sub_repl_streams':
    ReplayMode.sub_repl_streams(payload['data'])
  # ====================================================================================================================
  # SIMULATE MODE
  # ====================================================================================================================
  # TODO implement this
  # ====================================================================================================================
  # FALLBACK
  # ====================================================================================================================
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
