import json
import logging
from typing import Union, List, Type, Callable, Any

import websockets

logger = logging.getLogger()


class LiveStreamQuery:

  def __init__(self, source_id: str, name: str, attributes: dict) -> None:
    super().__init__()
    self.source_id = source_id
    self.name = name
    self.attributes = attributes

  def gen_pred_str(self):
    return ""


class ReplStreamQuery:

  def __init__(self, dataset: str, source_id: str, name: str, attributes: dict) -> None:
    super().__init__()
    self.dataset = dataset
    self.source_id = source_id
    self.name = name
    self.attributes = attributes

  def gen_pred_str(self):
    return ""


class SimlStreamQuery:

  def __init__(self, source_id: str, name: str, attributes: dict) -> None:
    super().__init__()
    self.source_id = source_id
    self.name = name
    self.attributes = attributes

  def gen_pred_str(self):
    return ""


class DatasetQuery:

  def __init__(self, name: str) -> None:
    super().__init__()
    self.name = name

  @property
  def name(self):
    return self.name

  @name.setter
  def name(self, value):
    self.name = value


class DataMuxClient:

  def __init__(self, uri: str) -> None:
    super().__init__()
    self.ws = ...
    self.uri = uri

  async def connect(self):
    logger.debug(f"connecting to websocket server: {self.uri}...")
    self.ws = await websockets.connect(self.uri)
    logger.debug(f"connected to websocket server: {self.uri}")

  async def disconnect(self):
    logger.debug(f"disconnecting from websocket server: {self.uri}...")
    await self.ws.close()
    logger.debug(f"disconnected from websocket server: {self.uri}")

  async def get_datasets(self):
    logger.debug(f"requesting available datasets...")
    await self.ws.send(json.dumps({'command': 'get_datasets'}))
    msg = await self.ws.recv()
    json_msg = json.loads(msg)
    if json_msg['command'] == 'datasets':
      datasets = json_msg['data']['datasets']
      return datasets
    return None

  async def get_live_streams(self):
    logger.debug(f"requesting live streams...")
    # get live streams
    await self.ws.send(json.dumps({'command': 'get_live_streams'}))
    msg = await self.ws.recv()
    json_msg = json.loads(msg)
    if json_msg['command'] == 'live_streams':
      live_streams = json_msg['data']['streams']
      return live_streams
    return None

  async def get_repl_streams(self, dataset: str):
    logger.debug(f"requesting repl streams for dataset: {dataset}")
    # get repl streams
    await self.ws.send({'command': 'get_repl_streams', 'data': {'dataset_name': dataset}})

  async def get_siml_streams(self):
    logger.debug(f"requesting available siml streams...")
    await self.ws.send()

  async def sub_live_stream(self, stream: Union[LiveStreamQuery, List[LiveStreamQuery]]):
    logger.debug(f"subscribing to live stream: {stream}")
    await self.ws.send()

  async def sub_repl_stream(self, stream: Union[ReplStreamQuery, List[ReplStreamQuery]]):
    logger.debug(f"subscribing to repl stream: {stream}")
    await self.ws.send()

  async def sub_siml_stream(self, stream: SimlStreamQuery):
    logger.debug(f"subscribing to siml stream: {stream}")
    await self.ws.send()

  @staticmethod
  def __parse_arg(arg, arg_name: str, cls: Type, fn: Callable[[Any], str]) -> Union[None, str, List[str]]:
    result = []
    if arg is None:
      return None
    if isinstance(arg, List):
      for x in arg:
        if not isinstance(x, cls):
          raise ValueError(f"'{arg_name}' type should be either {cls} or List[{cls}]")
        else:
          result.append(fn(x))
    elif isinstance(arg, cls):
      result.append(fn(arg))
    else:
      raise ValueError(f"'{arg_name}' type should be either {cls} or List[{cls}]")
    return result
