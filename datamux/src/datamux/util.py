import asyncio
import importlib
import logging
import random
import sys
from functools import wraps, partial
from typing import Dict, Any, Union, List, Generator, Tuple, Callable, Iterator

import numpy as np
from pylsl import StreamInfo, XMLElement, StreamInlet, LostError

from dfs import DataSetSpec, get_meta_dir

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]

KNOWN_ARRAY_ELEMENTS = ['channels']
logger = logging.getLogger()


def gen_dict(e: XMLElement, depth=0) -> Union[DICT, List[Any], str]:
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
    p = gen_dict(child, depth + 1)
    if isinstance(d, dict):
      d[child.name()] = p
    elif isinstance(d, list):
      d.append(p)
    child = child.next_sibling()
  return d


def gen_stream_info_dict(x: Union[StreamInfo, StreamInlet]):
  def fn(i: StreamInfo):
    return {'source': i.source_id(), 'channel_count': i.channel_count(), 'name': i.name(), 'type': i.type(),
            **gen_dict(i.desc())}

  if isinstance(x, StreamInfo):
    temp_inlet = StreamInlet(x)
    result = fn(temp_inlet.info())
    temp_inlet.close_stream()
  elif isinstance(x, StreamInlet):
    result = fn(x.info())
  else:
    raise RuntimeError('Invalid object type')
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


async def start_live_stream(stream: StreamInlet, queue: asyncio.Queue):
  logger.info('initializing live stream')
  s_info = gen_stream_info_dict(stream)
  logger.info('started live stream')
  while True:
    try:
      samples, timestamps, error = pull_lsl_stream_chunk(stream)
      if error:
        raise error
      if len(samples) == 0:
        await asyncio.sleep(0.0)
      else:
        res = {
          'command': 'data',
          'data': {
            'stream': {
              'source': s_info['source'],
              'type': s_info['type'],
              'attributes': s_info['attributes']
            },
            'index': timestamps,
            'chunk': np.nan_to_num(samples, nan=-1).tolist()
          }
        }
        await queue.put(res)
    except LostError:
      break
  logger.info('ended live stream')


async def start_repl_stream(
  spec: DataSetSpec, repl_stream: DICT_GENERATOR, s_source: str, s_type: str, s_attrs: DICT, queue: asyncio.Queue
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
    await queue.put(res)
    await asyncio.sleep(dt)
  # end of data stream
  logger.info(f'ended replay')


def pull_lsl_stream_chunk(stream: StreamInlet, timeout: float = 0.0):
  try:
    sample, timestamps = stream.pull_chunk(timeout)
    return sample, timestamps, None
  except Exception as e:
    logger.info(f'LSL connection lost')
    return None, None, e


def asyncify(func, executor):
  @wraps(func)
  async def run(*args, **kwargs):
    return asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

  return run


if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
