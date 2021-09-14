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
    'id': x.source_id(),
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
  stream_info = stream.info()
  s_source = stream_info.source_id()
  s_type = stream_info.type()
  s_attrs = map_live_stream_info_to_dict(stream_info)
  # TODO find what works best between a per-stream single-threaded executor and a per-client multi-threaded executor
  with ThreadPoolExecutor(max_workers=1) as executor:
    while True:
      try:
        samples, timestamps, error = await asyncify(pull_lsl_stream_chunk, executor)(stream, 0.0)
        if error:
          raise error
        if len(samples) == 0:
          continue
        await queue.put({
          'command': 'data',
          'data': {
            'stream': {
              'source': s_source,
              'type': s_type,
              'attributes': s_attrs
            },
            'chunk': np.nan_to_num(samples, nan=-1).tolist()
          }
        })
      except LostError:
        break
    logger.debug('streams unsubscribed')


async def start_repl_stream(
  spec: DataSetSpec,
  repl_stream: DICT_GENERATOR,
  s_source: str,
  s_type: str,
  s_attrs: DICT,
  queue: asyncio.Queue
):
  # TODO find what works best between a per-stream single-threaded executor and a per-client multi-threaded executor
  with ThreadPoolExecutor(max_workers=1) as executor:
    logger.info(f'Started replay')
    # get each sample of data from repl_stream
    for sample in repl_stream:
      await queue.put({
        'command': 'data',
        'data': {
          'stream': {
            'source': s_source,
            'type': s_type,
            'attributes': s_attrs
          },
          'chunk': [sample]
        }
      })
      # sleep until next cycle
      # --------- TODO copy pasted code, fix it ---------
      index = float(data[next(iter(stream.index))])  # assuming single-level indexes
      sample = [float(data[ch]) if data[ch] else np.nan for ch in stream.channels]
      if not all([i == np.nan for i in sample]):
        ts = time_ns() * 1e-9
        # push sample if consumers are available, and data exists
        outlet.push_sample(sample, index)
        # update prev_dt
        if prev_ts is not None:
          prev_dt = ts - prev_ts
        # update prev_ts
        prev_ts = ts
      # sleep for dt + correction to maintain stream frequency
      # --------- TODO end of copy pasted code ---------
      await asyncio.sleep(dt + (dt - prev_dt))
    # end of data stream
    logger.info(f'Replay ended')


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
