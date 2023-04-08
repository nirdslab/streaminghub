import asyncio
import importlib
import logging
import random
import sys
from pathlib import Path
from typing import List, Dict, Union, Iterator, Tuple, Callable, Any

import numpy as np

import dfds
from .util import DICT, DICT_GENERATOR

logger = logging.getLogger()


class ReplayMode:

  @staticmethod
  def get_datasets():
    dataset_names = [*map(lambda x: x.name[:-5], Path(dfds.get_dataset_dir()).glob("*.json"))]
    dataset_specs: List[dfds.DataSetSpec] = [*map(dfds.get_dataset_spec, dataset_names)]
    return {
      'command': 'datasets',
      'data': {'datasets': dict(zip(dataset_names, dataset_specs))},
      'error': None
    }

  @staticmethod
  def get_repl_streams(dataset_name: str):
    dataset_spec = dfds.get_dataset_spec(dataset_name)
    repl_stream_info: List[Dict[str, Union[str, dict]]] = []
    for repl_stream, s_attrs in ReplayMode.find_repl_streams(dataset_spec):
      logger.debug("repl stream: %s", s_attrs)
      sources = dataset_spec.sources
      for source_id in sources:
        source = sources[source_id]
        streams = source.streams
        for stream_id in streams:
          stream = streams[stream_id]
          repl_stream_info.append({
            'source': source_id,
            'device': source.device,
            'mode': 'repl',
            'stream_id': stream_id,
            'stream': stream,
            'attributes': s_attrs
          })
    return {
      'command': 'repl_streams',
      'data': {'streams': repl_stream_info},
      'error': None
    }

  @staticmethod
  def sub_repl_streams(data: List[Dict[str, Union[str, dict]]], queue: asyncio.Queue):
    # dataset = <dataset_id> | source = <source_id> | type = <stream_id>
    stream_query = [(
      str(d.get('attributes').get('dataset')),
      str(d.get('source', '')),
      str(d.get('stream_id', '')),
      dict(d.get('attributes', {}))
    ) for d in data]
    # count of queries and tasks
    num_queries = len(stream_query)
    num_tasks = 0
    # iterate each query and start repl streams
    for sq_dataset, sq_source, sq_stream_id, sq_attrs in stream_query:
      # expand sq_attrs into array form. TODO find a better alternative
      sq_attrs_arr = {}
      for k in sq_attrs.keys():
        if k == 'dataset':
          sq_attrs_arr[k] = sq_attrs[k]
        else:
          sq_attrs_arr[k] = [sq_attrs[k]]

      dataset_spec = dfds.get_dataset_spec(sq_dataset)
      for repl_stream, s_attrs in ReplayMode.find_repl_streams(dataset_spec, **sq_attrs_arr):
        # create task to replay data
        logger.info([sq_source, sq_stream_id, s_attrs])
        asyncio.create_task(ReplayMode.start_repl_stream(dataset_spec, repl_stream, sq_source, sq_stream_id, s_attrs, queue))
        num_tasks += 1
    logger.info("started %d repl stream tasks for the %d queries", num_tasks, num_queries)
    # return notification and coroutines
    return {
      'command': 'notification',
      'data': {'message': f'started {num_tasks} repl stream tasks for the {num_queries} queries'},
      'error': None
    }

  @staticmethod
  def find_repl_streams(spec: dfds.DataSetSpec, **kwargs) -> Iterator[Tuple[DICT_GENERATOR, DICT]]:
    if dfds.get_meta_dir() not in sys.path:
      sys.path.append(dfds.get_meta_dir())
    resolver = importlib.import_module(f'resolvers.{spec.name}')
    stream: Callable[[dfds.DataSetSpec, ...], Any] = getattr(resolver, 'stream')
    yield from stream(spec, **kwargs)

  @staticmethod
  async def start_repl_stream(
    spec: dfds.DataSetSpec, repl_stream: DICT_GENERATOR, s_source: str, s_stream_id: str, s_attrs: DICT, queue: asyncio.Queue
  ):
    logger.info(f'started replay')
    # prepare static vars
    stream_info = spec.sources[s_source].streams[s_stream_id]
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
            'name': s_stream_id,
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
