import asyncio
import logging
from threading import Thread

from pylsl import StreamInfo as LiveStreamInfo
from pylsl import StreamInlet as LiveStreamInlet
from pylsl import resolve_bypred as resolve_live_streams_by_pred_str
from pylsl import resolve_streams as resolve_all_live_streams
from typing import List, Dict, Union, Tuple

from datamux.util import gen_stream_info_dict, start_live_stream

logger = logging.getLogger()


class RelayMode:

  @staticmethod
  def get_live_streams():
    live_streams = resolve_all_live_streams()
    return {
      'command': 'live_streams',
      'data': {'streams': [*map(gen_stream_info_dict, live_streams)]},
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
      asyncio.create_task(start_live_stream(inlet, queue))
      num_tasks += 1
    logger.info("started %d live stream tasks for the %d queries", num_tasks, num_queries)
    return {
      'command': 'notification',
      'data': {'message': f'started {num_tasks} live stream tasks for the {num_queries} queries'},
      'error': None
    }
