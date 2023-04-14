import asyncio
import importlib
import logging
import random
import sys
from typing import List, Dict, Union, Iterator, Tuple, Callable, Any

import numpy as np

from dfds import Parser
from dfds.dtypes import Collection, Node, Stream
from .util import DICT, DICT_GENERATOR

import glob

logger = logging.getLogger()


class ReplayMode:
    """_summary_

    Returns:
        _type_: _description_

    Yields:
        _type_: _description_
    """

    parser = Parser()
    collections: Dict[str, Collection] = {}

    def find_available_collections(
        self,
    ) -> Dict:
        for collection_path in glob.glob("dataloaders/*.collection.json"):
            metadata = ReplayMode.parser.get_collection_metadata(collection_path)
            collection_id = metadata.name
            self.collections[collection_id] = metadata
        return {
            "command": "collections.ls",
            "data": {"collections": self.collections},
            "error": None,
        }

    def get_available_streams(
        self,
        collection_id: str,
    ) -> Dict:
        metadata = self.collections[collection_id]
        streams: List[Dict[str, Union[str, list, dict]]] = []

        ## convert group query into a URL query parameter??

        for stream_id, stream in metadata.streams.items():
            logger.debug(f"{collection_id}, stream: {stream_id:%d}")
            node: Node = stream.node
            streams.append(
                {
                    "source": str(hash(node.device or node.uri)),
                    "device": str(node.device),
                    "mode": "repl",
                    "id": stream_id,
                    "name": stream.name,
                    "description": stream.description,
                    "fields": list(stream.fields.keys()),
                    "attributes": {k: v.values for k, v in metadata.groups.items()},
                }
            )
        return {
            "command": "collection.streams.ls",
            "data": {"streams": streams},
            "error": None,
        }

    def subscribe_to_stream(
        self,
        query: Dict[str, str],
        stream: Stream,
        queue: asyncio.Queue,
    ):
        # dataset = <dataset_id> | source = <source_id> | type = <stream_id>
        # stream_query = (
        #     str(d.get("attributes").get("dataset")),
        #     str(d.get("source", "")),
        #     str(d.get("stream_id", "")),
        #     dict(d.get("attributes", {})),
        # )

        # count of queries and tasks
        num_queries =  len(query)
        num_tasks = 0

        # expand sq_attrs into array form.
        # TODO find a better alternative.
        sq_attrs_arr = {}
        for k in query:
            if k == "dataset":
                sq_attrs_arr[k] = sq_attrs[k]
            else:
                sq_attrs_arr[k] = [sq_attrs[k]]

            dataset_spec = dfds.get_dataset_spec(sq_dataset)
            for repl_stream, s_attrs in ReplayMode.find_repl_streams(
                dataset_spec, **sq_attrs_arr
            ):
                # create task to replay data
                logger.info([sq_source, sq_stream_id, s_attrs])
                asyncio.create_task(
                    ReplayMode.start_repl_stream(
                        dataset_spec,
                        repl_stream,
                        sq_source,
                        sq_stream_id,
                        s_attrs,
                        queue,
                    )
                )
                num_tasks += 1
        logger.info(
            "started %d repl stream tasks for the %d queries", num_tasks, num_queries
        )
        # return notification and coroutines
        return {
            "command": "notification",
            "data": {
                "message": f"started {num_tasks} repl stream tasks for the {num_queries} queries"
            },
            "error": None,
        }

    @staticmethod
    def find_repl_streams(
        spec: dfds.DataSetSpec,
        **kwargs,
    ) -> Iterator[Tuple[DICT_GENERATOR, DICT]]:
        if dfds.get_meta_dir() not in sys.path:
            sys.path.append(dfds.get_meta_dir())
        resolver = importlib.import_module(f"resolvers.{spec.name}")
        stream: Callable[[dfds.DataSetSpec, ...], Any] = getattr(resolver, "stream")
        yield from stream(spec, **kwargs)

    @staticmethod
    async def start_repl_stream(
        spec: dfds.DataSetSpec,
        repl_stream: DICT_GENERATOR,
        s_source: str,
        s_stream_id: str,
        s_attrs: DICT,
        queue: asyncio.Queue,
    ):
        logger.info(f"started replay")
        # prepare static vars
        stream_info = spec.sources[s_source].streams[s_stream_id]
        f = stream_info.frequency
        index_cols = [*stream_info.index.keys()]
        # get each sample of data from repl_stream
        for data in repl_stream:
            # prepare dynamic vars
            dt = (1.0 / f) if f > 0 else (random.randrange(0, 10) / 10.0)
            timestamp = [data[col] for col in index_cols][0]  # assume 1D temporal index
            sample = [
                float(data[ch]) if data[ch] else np.nan for ch in stream_info.channels
            ]
            res = {
                "command": "data",
                "data": {
                    "stream": {
                        "source": s_source,
                        "name": s_stream_id,
                        "attributes": s_attrs,
                    },
                    "index": [timestamp],
                    "chunk": [sample],
                },
            }
            await queue.put(res)
            await asyncio.sleep(dt)
        # end of data stream
        logger.info(f"ended replay")
