import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Union

import dfs
from datamux.util import find_repl_streams, start_repl_stream

logger = logging.getLogger()


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
  def sub_repl_streams(data: List[Dict[str, Union[str, dict]]], queue: asyncio.Queue):
    # dataset = <dataset_id> | source = <source_id> | type = <stream_id>
    stream_query = [(
      str(d.get('dataset', '')),
      str(d.get('source', '')),
      str(d.get('type', '')),
      dict(d.get('attributes', {}))
    ) for d in data]
    # count of queries and tasks
    num_queries = len(stream_query)
    num_tasks = 0
    # iterate each query and start repl streams
    for sq_dataset, sq_source, sq_type, sq_attrs in stream_query:
      dataset_spec = dfs.get_dataset_spec(sq_dataset)
      for repl_stream, s_attrs in find_repl_streams(dataset_spec, **sq_attrs):
        # create task to replay data
        asyncio.create_task(start_repl_stream(dataset_spec, repl_stream, sq_source, sq_type, s_attrs, queue))
    logger.info("started %d repl stream tasks for the %d queries", num_tasks, num_queries)
    # return notification and coroutines
    return {
      'command': 'notification',
      'data': {'message': f'started {num_tasks} repl stream tasks for the {num_queries} queries'},
      'error': None
    }
