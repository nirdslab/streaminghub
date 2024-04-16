import logging
import random
import time
import timeit
from multiprocessing import Queue
from threading import Event
from typing import Callable

import numpy as np
import pylsl
import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

from .util import stream_to_stream_info


class CollectionManager(datamux.Reader[dfds.Collection], datamux.IServe):
    """
    Stream Reader for DFDS Collections.

    Functions:
    * attach(source_id, stream_id, q, **kwargs)
    * serve(source_id, stream_id, **kwargs)
    * list_sources()
    * list_streams(source_id)

    """

    __parser = dfds.Parser()
    __collections: list[dfds.Collection] = []
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        config: dfds.Config,
    ) -> None:
        super().__init__()
        self.config = config

    def setup(self, **kwargs) -> None:
        # nothing to set up for collection manager
        return None

    def list_sources(
        self,
    ) -> list[dfds.Collection]:
        self._refresh_sources()
        return self.__collections

    def list_streams(
        self,
        source_id: str,
    ) -> list[dfds.Stream]:
        collection = [c for c in self.__collections if c.name == source_id][0]
        streams = []
        dataloader = collection.dataloader(self.config)
        for attrs in dataloader.ls():
            for stream_id, stream in collection.streams.items():
                stream = stream.model_copy(deep=True)
                stream.attrs.update(attrs)
                stream.attrs.update({"id": stream_id})
                streams.append(stream)
        return streams

    def _refresh_sources(
        self,
    ) -> None:
        self.__collections.clear()
        for fp in self.config.meta_dir.glob("*.collection.json"):
            collection = self.__parser.get_collection_metadata(fp.as_posix())
            self.__collections.append(collection)

    def _attach_coro(
        self,
        source_id: str,
        stream_id: str,
        q: Queue,
        *,
        attrs: dict,
        transform: Callable,
        flag: Event,
        strict_time: bool = True,
        use_relative_timestamps: bool = True,
    ):
        collection = [c for c in self.__collections if c.name == source_id][0]
        stream = [s.model_copy() for s in collection.streams.values() if s.name == stream_id][0]
        stream.attrs.update(attrs, dfds_mode="replay")
        freq = stream.frequency
        if freq <= 0:
            freq = random.randint(1, 50)  # assign a random frequency between 0 and 50
        dt = 1 / freq
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader(self.config).read(stream.attrs)
        stream.attrs.update(attrs)

        # termination indicator
        eof = datamux.END_OF_STREAM
        if transform is not None:
            eof = transform(eof)

        # preprocessing
        data = data.sort_values(index_cols, ascending=True)
        # if index not present, create one with given frequency
        for col in index_cols:
            if col not in data.columns:
                data[col] = np.arange(len(data)) / freq
        # always convert time to seconds
        primary_index = index_cols[0]
        dt_true = float(data.iloc[1][primary_index] - data.iloc[0][primary_index])
        si_scales = np.array([1, 1e3, 1e6, 1e9], dtype=int)
        scale = si_scales[np.abs(si_scales - dt_true / dt).argmin()]
        data[primary_index] = data[primary_index] / scale

        # replay each record
        self.logger.info(f"replay started")
        t0, T0 = None, None
        for _, record in data.iterrows():
            # terminating condition
            if flag.is_set():
                self.logger.info(f"replay stop requested")
                break

            # create record
            index = {k: record[k] for k in index_cols}
            value = {k: record[k] for k in value_cols}

            # wait until time requirements are met
            if strict_time:
                if t0 is None or T0 is None:
                    t0, T0 = timeit.default_timer(), index[index_cols[0]]
                else:
                    ti, Ti = timeit.default_timer(), index[index_cols[0]]
                    dt = (Ti - T0) - (ti - t0)
                    if dt > 0:
                        time.sleep(dt)
            else:
                time.sleep(dt)

            # postprocessing
            if use_relative_timestamps:
                index[index_cols[0]] -= T0

            # send record
            msg = dict(index=index, value=value)
            if transform is not None:
                msg = transform(msg)
            q.put_nowait(msg)

        q.put_nowait(eof)
        self.logger.info(f"replay ended")

    def _serve_coro(
        self,
        source_id: str,
        stream_id: str,
        *,
        attrs: dict,
    ):
        collection = [c for c in self.__collections if c.name == source_id][0]
        stream = [s.model_copy() for s in collection.streams.values() if s.name == stream_id][0]
        stream.attrs.update(attrs, dfds_mode="restream")
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
