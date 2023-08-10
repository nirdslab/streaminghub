import asyncio
import glob
import logging
import random
from typing import List

import pylsl
from dfds import Parser
from dfds.typing import Collection, Stream

from . import Reader
from pathlib import Path
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
        for fp in Path.cwd().joinpath("repository").resolve().glob("*.collection.json"):
            collection = self.__parser.get_collection_metadata(fp.as_posix())
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
                stream = stream.model_copy(deep=True)
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
        if freq <= 0:
            freq = random.randint(1, 50)  # assign a random frequency between 0 and 50
        dt = 1 / freq
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader().read(stream.attrs)
        stream.attrs.update(attrs)

        # replay each record
        logger.info(f"started replay")
        for record in data:
            index = dict(zip(index_cols, record[index_cols].item()))
            value = dict(zip(value_cols, record[value_cols].item()))
            await queue.put((b"data", dict(index=index, value=value)))
            await asyncio.sleep(dt)
        logger.info(f"ended replay")

    async def __restream_coro(
        self,
        collection: Collection,
        stream: Stream,
    ):
        freq = stream.frequency
        if freq <= 0:
            freq = random.randint(1, 50)  # assign a random frequency between 0 and 50
        dt = 1 / freq
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader().read(stream.attrs)
        stream.attrs.update(attrs)

        outlet = pylsl.StreamOutlet(stream_to_stream_info(stream))
        num_samples = data.shape[0]
        current_index = 0

        # restream each record
        logger.info(f"started restream: dt={dt:.4f}, n={num_samples}")
        while current_index < num_samples:
            index = data[current_index][index_cols]
            value = data[current_index][value_cols]
            if outlet.have_consumers():
                # FIXME currently only supports 1D index
                outlet.push_sample(value.tolist(), index[0])
                current_index += 1
            await asyncio.sleep(dt)
        logger.info(f"ended restream")
