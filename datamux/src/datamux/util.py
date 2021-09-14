import asyncio
import importlib
import logging
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, partial
from typing import Dict, Any, Union, List, Generator, Tuple, Callable, Iterator

import numpy as np
from pylsl import StreamInfo as LSLStreamInfo, XMLElement, StreamInlet, LostError

from dfs import DataSetSpec, get_meta_dir

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]

KNOWN_ARRAY_ELEMENTS = ['channels']
logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
logger = logging.getLogger()


def map_live_stream_desc_to_dict(e: XMLElement, depth=0) -> Union[DICT, List[Any], str]:
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
    p = map_live_stream_desc_to_dict(child, depth + 1)
    if isinstance(d, dict):
      d[child.name()] = p
    elif isinstance(d, list):
      d.append(p)
    child = child.next_sibling()
  return d


def map_live_stream_info_to_dict(x: Union[LSLStreamInfo, StreamInlet]):
  if isinstance(x, LSLStreamInfo):
    temp_inlet = StreamInlet(x)
    desc = temp_inlet.info().desc()
    temp_inlet.close_stream()
  elif isinstance(x, StreamInlet):
    desc = x.info().desc()
  else:
    raise RuntimeError("the argument 'x' is neither a StreamInfo nor a StreamInlet")
  result = {
    'source': x.source_id(),
    'channel_count': x.channel_count(),
    'name': x.name(),
    'type': x.type(),
    **map_live_stream_desc_to_dict(desc)
  }
  return result


def find_repl_streams(
  spec: DataSetSpec,
  **kwargs
) -> Iterator[Tuple[DICT_GENERATOR, DICT]]:
  if get_meta_dir() not in sys.path:
    sys.path.append(get_meta_dir())
  resolver = importlib.import_module(f'resolvers.{spec.name}')
  stream: Callable[[DataSetSpec, ...], Any] = getattr(resolver, 'stream')
  yield from stream(spec, **kwargs)


async def start_live_stream(
  stream: StreamInlet,
  queue: asyncio.Queue
):
  logger.debug('initializing live stream')
  stream_info = stream.info()
  s_source = stream_info.source_id()
  s_type = stream_info.type()
  s_attrs = map_live_stream_info_to_dict(stream_info)
  logger.debug('started live stream')
  # TODO find what works best between a per-stream single-threaded executor and a per-client multi-threaded executor
  with ThreadPoolExecutor(max_workers=1) as executor:
    while True:
      try:
        samples, timestamps, error = await asyncify(pull_lsl_stream_chunk, executor)(stream, 0.0)
        if error:
          raise error
        if len(samples) == 0:
          continue
        res = {
          'command': 'data',
          'data': {
            'stream': {
              'source': s_source,
              'type': s_type,
              'attributes': s_attrs
            },
            'index': timestamps,
            'chunk': np.nan_to_num(samples, nan=-1).tolist()
          }
        }
        logger.info(res)
        await queue.put(res)
      except LostError:
        break
  logger.debug('ended live stream')


async def start_repl_stream(
  spec: DataSetSpec,
  repl_stream: DICT_GENERATOR,
  s_source: str,
  s_type: str,
  s_attrs: DICT,
  queue: asyncio.Queue
):
  logger.info(f'started replay')
  # prepare static vars
  stream_info = spec.sources[s_source].streams[s_type]
  f = stream_info.frequency
  index_cols = [*stream_info.index.keys()]
  # get each sample of data from repl_stream
  for data in repl_stream:
    # prepare dynamic vars
    dt = (1. / f) if f > 0 else (random.randrange(0, 10) / 10.0)
    timestamp = [data[col] for col in index_cols][0]  # assume 1D temporal index
    sample = [float(data[ch]) if data[ch] else np.nan for ch in stream_info.channels]
    res = {
      'command': 'data',
      'data': {
        'stream': {
          'source': s_source,
          'type': s_type,
          'attributes': s_attrs
        },
        'index': [timestamp],
        'chunk': [sample]
      }
    }
    logger.info(res)
    await queue.put(res)
    await asyncio.sleep(dt)
  # end of data stream
  logger.info(f'ended replay')


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
    return asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

  return run
