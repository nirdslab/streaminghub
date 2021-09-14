import asyncio
import logging
from typing import List, Dict, Union

from pylsl import StreamInfo as LiveStreamInfo
from pylsl import StreamInlet as LiveStreamInlet
from pylsl import resolve_bypred as resolve_live_streams_by_pred_str
from pylsl import resolve_streams as resolve_all_live_streams

from datamux.util import map_live_stream_info_to_dict, start_live_stream

logger = logging.getLogger()


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
  def sub_live_streams(data: List[Dict[str, Union[str, dict]]], loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
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
    # count of queries and tasks
    num_queries = len(stream_query)
    num_tasks = 0
    # run one query to get a superset of the requested streams
    available_live_stream_info: List[LiveStreamInfo] = resolve_live_streams_by_pred_str(pred_str)
    # iterate each query and start live streams
    for live_stream_info in available_live_stream_info:
      for (sq_source, sq_type, sq_attrs) in stream_query:
        if live_stream_info.source_id() == sq_source and live_stream_info.type() == sq_type:
          # compare attributes and select only if all attributes match
          s_attrs: dict = map_live_stream_info_to_dict(live_stream_info).get("attributes", {})
          if all(sq_attrs[k] == s_attrs.get(k, None) for k in sq_attrs):
            # create task to live-stream data
            inlet = LiveStreamInlet(live_stream_info, max_chunklen=1, recover=False)
            loop.create_task(start_live_stream(inlet, queue))
            num_tasks += 1
    logger.info("started %d live stream tasks for the %d queries", num_tasks, num_queries)
    return {
      'command': 'notification',
      'data': {'message': f'started {num_tasks} live stream tasks for the {num_queries} queries'},
      'error': None
    }
