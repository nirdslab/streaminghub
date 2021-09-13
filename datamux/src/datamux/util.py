import asyncio
import importlib
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, partial
from typing import Dict, Any, Union, List, Generator, Tuple, Callable, Iterator

import numpy as np
from pylsl import StreamInfo as LSLStreamInfo, XMLElement, StreamInlet, LostError

from dfs import DataSetSpec, get_meta_dir
from dfs.types import DeviceInfo, StreamInfo

KNOWN_ARRAY_ELEMENTS = ['channels']
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()


def map_stream_desc_to_dict(e: XMLElement, depth=0) -> Union[Dict[str, Any], List[Any], str]:
  # terminal case(s)
  if e.empty():
    return {}
  if e.is_text():
    return e.value()
  if e.first_child().is_text():
    return e.first_child().value()
  # check whether parsing a known array element
  d = [] if e.name() in KNOWN_ARRAY_ELEMENTS else {}
  # parse all children
  child = e.first_child()
  while not child.empty():
    p = map_stream_desc_to_dict(child, depth + 1)
    if isinstance(d, dict):
      d[child.name()] = p
    elif isinstance(d, list):
      d.append(p)
    child = child.next_sibling()
  return d


def map_lsl_stream_info_to_dict(x: LSLStreamInfo):
  temp_inlet = StreamInlet(x)
  desc = temp_inlet.info().desc()
  result = {
    'id': x.source_id(),
    'channel_count': x.channel_count(),
    'name': x.name(),
    'type': x.type(),
    **map_stream_desc_to_dict(desc)
  }
  temp_inlet.close_stream()
  return result


def dataset_attrs_and_data(spec: DataSetSpec, dataset_name: str, **kwargs) -> Iterator[
  Tuple[Dict[str, Any], Generator[Dict[str, float], None, None]]]:
  if get_meta_dir() not in sys.path:
    sys.path.append(get_meta_dir())
  resolver = importlib.import_module(f'resolvers.{dataset_name}')
  stream: Callable[[DataSetSpec, ...], Any] = getattr(resolver, 'stream')
  yield from stream(spec, **kwargs)


async def proxy_lsl_stream(stream: StreamInlet, responses: asyncio.Queue):
  # TODO find what works best between a per-stream single-threaded executor and a per-client multi-threaded executor
  with ThreadPoolExecutor(max_workers=1) as executor:
    while True:
      try:
        samples, timestamps, error = await asyncify(pull_lsl_stream_chunk, executor)(stream, 0.0)
        if error:
          raise error
        typ = stream.info().type()
        if len(samples) == 0:
          continue
        await responses.put(
          {'command': 'data', 'data': {'stream': typ, 'chunk': np.nan_to_num(samples, nan=-1).tolist()}})
      except LostError:
        break
    logger.debug('streams unsubscribed')

async def replay_data(
  stream: StreamInfo,
  device: DeviceInfo,
  attrs: Dict[str, Any], data:  Generator[Dict[str, float], None, None], responses: asyncio.Queue):
  # TODO find what works best between a per-stream single-threaded executor and a per-client multi-threaded executor
  with ThreadPoolExecutor(max_workers=1) as executor:
    logger.info(f'Started replay')
    for sample in data:
      await responses.put(
        {'command': 'data', 'data': {'stream': typ, 'chunk': sample}})
    task = loop.create_task(emit(outlet, data_stream, stream_info))
    logger.info(f'Ended replay')


def pull_lsl_stream_chunk(stream: StreamInlet, timeout: float):
  try:
    sample, timestamps = stream.pull_chunk(timeout)
    return sample, timestamps, None
  except Exception as e:
    logger.debug(f'LSL connection lost')
    return None, None, e


def asyncify(func, executor):
  @wraps(func)
  async def run(*args, **kwargs):
    return await asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

  return run
