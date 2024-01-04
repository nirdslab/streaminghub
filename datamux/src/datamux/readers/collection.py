import logging
import random
import time
from multiprocessing import Queue
from threading import Event, Thread

import pylsl
from dfds import Parser
from dfds.typing import Collection, Stream, Config

import datamux.util as util

from . import Reader
from .util import stream_to_stream_info


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
    __collections: list[Collection] = []
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        config: Config,
    ) -> None:
        super().__init__()
        self.config = config

    def list_collections(
        self,
    ) -> list[Collection]:
        return self.__collections

    def refresh_collections(
        self,
    ) -> None:
        self.__collections.clear()
        for fp in self.config.meta_dir.glob("*.collection.json"):
            collection = self.__parser.get_collection_metadata(fp.as_posix())
            self.__collections.append(collection)

    def list_streams(
        self,
        collection_name: str,
    ) -> list[Stream]:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        streams = []
        dataloader = collection.dataloader(self.config)
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
        queue: Queue,
        transform,
        flag,
    ) -> None:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        stream = [s for s in collection.streams.values() if s.name == stream_name][0]
        stream.attrs.update(attrs, dfds_mode="replay")
        thread = Thread(None, self.replay_coro, stream_name, (collection, stream, queue, transform, flag), daemon=True)
        thread.start()

    def restream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
    ) -> None:
        collection = [c for c in self.__collections if c.name == collection_name][0]
        stream = [s for s in collection.streams.values() if s.name == stream_name][0]
        stream.attrs.update(attrs, dfds_mode="restream")
        thread = Thread(None, self.restream_coro, stream_name, (collection, stream), daemon=True)
        thread.start()

    def replay_coro(
        self,
        collection: Collection,
        stream: Stream,
        queue: Queue,
        transform,
        flag: Event,
    ):
        freq = stream.frequency
        if freq <= 0:
            freq = random.randint(1, 50)  # assign a random frequency between 0 and 50
        dt = 1 / freq
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader(self.config).read(stream.attrs)
        stream.attrs.update(attrs)

        # termination indicator
        eof = util.END_OF_STREAM
        if transform is not None:
            eof = transform(eof)

        # replay each record
        self.logger.info(f"replay started")
        for record in data:
            if flag.is_set():
                self.logger.info(f"replay stop requested")
                break

            index = dict(zip(index_cols, record[index_cols].item()))
            value = dict(zip(value_cols, record[value_cols].item()))
            msg = dict(index=index, value=value)

            if transform is not None:
                msg = transform(msg)

            queue.put_nowait(msg)
            time.sleep(dt)

        queue.put_nowait(eof)
        self.logger.info(f"replay ended")

    def restream_coro(
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

        attrs, data = collection.dataloader(self.config).read(stream.attrs)
        stream.attrs.update(attrs)

        outlet = pylsl.StreamOutlet(stream_to_stream_info(stream))
        num_samples = data.shape[0]
        current_index = 0

        # restream each record
        started = False
        self.logger.info(f"started restream: dt={dt:.4f}, n={num_samples}")
        while current_index < num_samples:
            index = data[current_index][index_cols]
            value = data[current_index][value_cols]
            if outlet.have_consumers():
                started = True
                x = value.tolist()
                t = index[0]  # FIXME currently only supports 1D index
                outlet.push_sample(x, t)
                current_index += 1
            elif started:
                # if no consumers after starting, stop restreaming
                break
            time.sleep(dt)
        self.logger.info(f"ended restream")
