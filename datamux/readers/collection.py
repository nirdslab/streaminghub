import asyncio
import glob
import logging
import random
from typing import List

import pylsl
from dfds import Parser
from dfds.typing import Collection, Stream

from . import Reader
from .util import stream_to_stream_info

logger = logging.getLogger()


# TODO change restreaming from pointwise to groupwise
class CollectionReader(Reader):
    """
    Stream Reader for DFDS Collections.

    Functions provided:

    * list_collections() - return a list of currently available collections

    * refresh_collections() - refresh the list of currently available collections

    * list_streams(collection_name) - list the streams in a collection

    * replay(collection_name, stream_name, queue) - replay data from a stream in a collection

    * restream(collection_name, stream_name) - restream (via lsl) data from a stream in a collection

    """

    __parser = Parser()
    __collections: List[Collection] = []

    def list_collections(
        self,
    ) -> List[Collection]:
        return self.__collections

    def refresh_collections(
        self,
    ) -> None:
        self.__collections.clear()
        for fp in sorted(glob.glob("repository/*.collection.json")):
            collection = self.__parser.get_collection_metadata(fp)
            self.__collections.append(collection)

    def list_streams(
        self,
        collection_name: str,
    ) -> List[Stream]:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        streams = []
        dataloader = collection.dataloader()
        for attrs in dataloader.ls():
            for stream_id, stream in collection.streams.items():
                stream = stream.copy()
                stream.attrs.update(attrs)
                stream.attrs.update({"id": stream_id})
                streams.append(stream)
        return streams

    def replay(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
        queue: asyncio.Queue,
    ) -> asyncio.Task:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        stream = [s for s in collection.streams.values() if s.name == stream_name][0]
        stream.attrs.update(attrs, dfds_mode="replay")
        return asyncio.create_task(
            self.__replay_coro(collection, stream, queue),
        )

    def restream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
    ) -> asyncio.Task:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        stream = [s for s in collection.streams.values() if s.name == stream_name][0]
        stream.attrs.update(attrs, dfds_mode="restream")
        return asyncio.create_task(
            self.__restream_coro(collection, stream),
        )

    async def __replay_coro(
        self,
        collection: Collection,
        stream: Stream,
        queue: asyncio.Queue,
    ):
        freq = stream.frequency
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader().read(stream.attrs)
        stream.attrs.update(attrs)

        # replay each record
        logger.info(f"started replay")
        for record in data:
            dt = (1.0 / freq) if freq > 0 else (random.randrange(0, 10) / 10.0)
            index = record[index_cols]
            value = record[value_cols]
            await queue.put(("data", dict(stream=stream, index=index, value=value)))
            await asyncio.sleep(dt)
        logger.info(f"ended replay")

    async def __restream_coro(
        self,
        collection: Collection,
        stream: Stream,
    ):
        freq = stream.frequency
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader().read(stream.attrs)
        stream.attrs.update(attrs)
        
        outlet = pylsl.StreamOutlet(stream_to_stream_info(stream))
        num_samples = data.shape[0]
        current_index = 0

        # restream each record
        logger.info(f"started restream")
        while current_index < num_samples:
            index = data[current_index][index_cols]
            value = data[current_index][value_cols]
            if outlet.have_consumers():
                outlet.push_sample(value, index)
                current_index += 1
            if freq > 0:
                dt = 1 / freq
            else:
                dt = random.randrange(1, 10) / 10.0
            await asyncio.sleep(dt)
        logger.info(f"ended restream")
