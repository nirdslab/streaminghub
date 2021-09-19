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
    """

    """
    logger.info("connecting to websocket server: %s...", self.uri)
    self.ws = await websockets.connect(self.uri)
    logger.info("connected to websocket server: %s", self.uri)

  async def disconnect(self):
    """

    """
    logger.info("disconnecting from websocket server: %s...", self.uri)
    await self.ws.close()
    logger.info("disconnected from websocket server: %s", self.uri)

  async def get_datasets(self):
    """

    :return:
    """
    logger.info("requesting available datasets...")
    await self.ws.send(json.dumps({'command': 'get_datasets'}))
    msg = await self.ws.recv()
    json_msg = json.loads(msg)
    if json_msg['command'] == 'datasets':
      datasets = json_msg['data']['datasets']
      logger.info("Received %d datasets", len(datasets))
      return datasets
    else:
      logger.warning("Response command was not 'datasets'")
      return None

  async def get_live_streams(self):
    """

    :return:
    """
    logger.info("requesting live streams...")
    # get live streams
    await self.ws.send(json.dumps({'command': 'get_live_streams'}))
    msg = await self.ws.recv()
    json_msg = json.loads(msg)
    if json_msg['command'] == 'live_streams':
      live_streams = json_msg['data']['streams']
      logger.info("Received %d live streams", len(live_streams))
      return live_streams
    else:
      logger.warning("Response command was not 'live_streams'")
      return None

  async def get_repl_streams(self, dataset: str):
    """

    :param dataset:
    :return:
    """
    logger.info("requesting repl streams for dataset: %s", dataset)
    # get repl streams
    await self.ws.send(json.dumps({'command': 'get_repl_streams', 'data': {'dataset_name': dataset}}))
    msg = await self.ws.recv()
    json_msg = json.loads(msg)
    if json_msg['command'] == 'repl_streams':
      repl_streams = json_msg['data']['streams']
      logger.info("Received %d repl streams for dataset: %s", len(repl_streams), dataset)
      return repl_streams
    else:
      logger.warning("Response command was not 'repl_streams'")
      return None

  async def get_siml_streams(self):
    logger.info("requesting available siml streams...")
    await self.ws.send()

  async def sub_live_stream(self, stream: Union[LiveStreamQuery, List[LiveStreamQuery]]):
    logger.info("subscribing to live stream: %s...", stream)
    await self.ws.send()

  async def sub_repl_stream(self, stream: Union[ReplStreamQuery, List[ReplStreamQuery]]):
    logger.info("subscribing to repl stream: %s...", stream)
    await self.ws.send()

  async def sub_siml_stream(self, stream: SimlStreamQuery):
    logger.info("subscribing to siml stream: %s...", stream)
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
