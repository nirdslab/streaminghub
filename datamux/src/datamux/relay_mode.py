import asyncio
import logging
from typing import List, Dict, Union, Tuple, Any

import numpy as np
from pylsl import StreamInfo as LiveStreamInfo, StreamInlet, LostError, XMLElement, StreamInfo
from pylsl import StreamInlet as LiveStreamInlet
from pylsl import resolve_bypred as resolve_live_streams_by_pred_str
from pylsl import resolve_streams as resolve_all_live_streams

from datamux.util import DICT

logger = logging.getLogger()
KNOWN_ARRAY_ELEMENTS = ['channels']


class RelayMode:

  @staticmethod
  def get_live_streams():
    live_streams = resolve_all_live_streams()
    return {
      'command': 'live_streams',
      'data': {'streams': [*map(RelayMode.gen_stream_info_dict, live_streams)]},
      'error': None
    }

  @staticmethod
  def sub_live_streams(data: List[Dict[str, Union[str, dict]]], queue: asyncio.Queue):
    # source = <source_id> | type = <stream_id>
    stream_query: List[Tuple[str, str, dict]] = [(
      str(d.get('source', '')),
      str(d.get('type', '')),
      dict(d.get('attributes', {}))
    ) for d in data]
    pred_str = ' or '.join(
      f"(source_id='{sq_source}' and type='{sq_type}' and " +
      " and ".join(f'desc/attributes/{x}="{sq_attrs[x]}"' for x in sq_attrs) +
      ')'
      for sq_source, sq_type, sq_attrs in stream_query
    )
    logger.debug('predicate: %s', pred_str)
    # count of queries and tasks
    num_queries = len(stream_query)
    num_tasks = 0
    # run one query to get a superset of the requested streams
    available_live_stream_info: List[LiveStreamInfo] = resolve_live_streams_by_pred_str(pred_str)
    logger.debug('found %d live stream match(es) for predicate', len(available_live_stream_info))
    # iterate each query and start live streams
    for live_stream_info in available_live_stream_info:
      # create task to live-stream data
      inlet = LiveStreamInlet(live_stream_info, max_chunklen=1, recover=False)
      asyncio.create_task(RelayMode.start_live_stream(inlet, queue))
      num_tasks += 1
    logger.info("started %d live stream tasks for the %d queries", num_tasks, num_queries)
    return {
      'command': 'notification',
      'data': {'message': f'started {num_tasks} live stream tasks for the {num_queries} queries'},
      'error': None
    }

  @staticmethod
  async def start_live_stream(stream: StreamInlet, queue: asyncio.Queue):
    logger.info('initializing live stream')
    s_info = RelayMode.gen_stream_info_dict(stream)
    logger.info('started live stream')
    while True:
      try:
        samples, timestamps, error = RelayMode.pull_lsl_stream_chunk(stream)
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

  @staticmethod
  def pull_lsl_stream_chunk(stream: StreamInlet, timeout: float = 0.0):
    try:
      sample, timestamps = stream.pull_chunk(timeout)
      return sample, timestamps, None
    except Exception as e:
      logger.info(f'LSL connection lost')
      return None, None, e

  @staticmethod
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
      p = RelayMode.gen_dict(child, depth + 1)
      if isinstance(d, dict):
        d[child.name()] = p
      elif isinstance(d, list):
        d.append(p)
      child = child.next_sibling()
    return d

  @staticmethod
  def gen_stream_info_dict(x: Union[StreamInfo, StreamInlet]):
    def fn(i: StreamInfo):
      return {'source': i.source_id(), 'channel_count': i.channel_count(), 'name': i.name(), 'type': i.type(),
              **RelayMode.gen_dict(i.desc())}

    if isinstance(x, StreamInfo):
      temp_inlet = StreamInlet(x)
      result = fn(temp_inlet.info())
      temp_inlet.close_stream()
    elif isinstance(x, StreamInlet):
      result = fn(x.info())
    else:
      raise RuntimeError('Invalid object type')
    return result
