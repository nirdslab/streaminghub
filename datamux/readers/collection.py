import asyncio
import glob
import logging
import random
from typing import List, OrderedDict

from dfds import Parser
from dfds.typing import Collection, Stream

from serializers import Serializer

from . import Reader

logger = logging.getLogger()


class CollectionReader(Reader):
    """
    Stream Reader for DFDS Collections

    """

    parser = Parser()
    collections: List[Collection] = []

    def get_collections(
        self,
    ) -> List[Collection]:
        return self.collections

    def refresh_collections(
        self,
    ) -> None:
        self.collections.clear()
        for fp in sorted(glob.glob("repository/*.collection.json")):
            collection = self.parser.get_collection_metadata(fp)
            self.collections.append(collection)

    def list_streams(
        self,
        collection: Collection,
        query: OrderedDict[str, str] = OrderedDict(),
    ) -> List[Stream]:
        streams = []
        assert collection in self.collections
        dataloader = collection.dataloader()
        for attrs in dataloader.ls():
            for stream_id, stream in collection.streams.items():
                stream.attrs.update(attrs)
                stream.attrs.update({"id": stream_id})
                streams.append(stream)
        return streams

    def read(
        self,
        collection: Collection,
        stream: Stream,
        queue: asyncio.Queue,
    ) -> asyncio.Task:
        serializer = Serializer(backend="json")
        return asyncio.create_task(
            self.restream_async(collection, stream, serializer, queue)
        )

    async def restream_async(
        self,
        collection: Collection,
        stream: Stream,
        serializer: Serializer,
        queue: asyncio.Queue,
    ):
        logger.info(f"started replay")
        freq = stream.frequency
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        # get each record of data
        attrs, data = collection.dataloader().read(stream.attrs)
        stream.attrs.update(attrs, dfds_runner="replay")
        # TODO change restreaming from pointwise to groupwise
        for record in data:
            dt = (1.0 / freq) if freq > 0 else (random.randrange(0, 10) / 10.0)
            index = record[index_cols]
            value = record[value_cols]
            message = serializer.encode("data", stream=stream, index=index, value=value)
            await queue.put(message)
            await asyncio.sleep(dt)

        # end of data stream
        logger.info(f"ended replay")
