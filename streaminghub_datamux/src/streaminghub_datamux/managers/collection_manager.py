import logging
import random
import time
from typing import Callable

import numpy as np

import streaminghub_datamux as dm
import streaminghub_pydfds as dfds


class CollectionManager(dm.Reader[dfds.Collection], dm.IServe):
    """
    Stream Reader for DFDS Collections.

    Functions:
    * attach(source_id, stream_id, q, **kwargs)
    * serve(source_id, stream_id, **kwargs)
    * list_sources()
    * list_streams(source_id)

    """

    __parser: dfds.Parser
    __collections: dict[str, dfds.Collection]

    def __init__(
        self,
        config: dfds.Config,
    ) -> None:
        super().__init__()
        self.config = config
        self.__parser = dfds.Parser()
        self.__collections = dict()

    def setup(self, **kwargs) -> None:
        self._refresh_sources()

    def list_sources(
        self,
    ) -> list[dfds.Collection]:
        return list(self.__collections.values())

    def list_streams(
        self,
        source_id: str,
    ) -> list[dfds.Stream]:
        collection = self.__collections[source_id]
        streams = []
        dataloader = collection.dataloader(self.config)
        for attrs in dataloader.ls():
            for stream_id, stream in collection.streams.items():
                stream = stream.model_copy(deep=True)
                if stream.node is None:
                    stream.node = dfds.Node(id=source_id)
                stream.attrs.update(attrs)
                stream.attrs.update({"id": stream_id, "mode": "replay"})
                streams.append(stream)
        return streams

    def _refresh_sources(
        self,
    ) -> None:
        self.__collections.clear()
        for fp in self.config.meta_dir.glob("*.collection.json"):
            id = fp.name[:-16]
            collection = self.__parser.get_collection_metadata(fp.as_posix())
            self.logger.info(f"Found collection: {collection.name}")
            self.__collections[id] = collection

    def on_attach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: dm.Queue,
        transform: Callable,
    ) -> dict:
        collection = self.__collections[source_id]
        stream = collection.streams[stream_id].model_copy()
        stream.attrs.update(attrs, dfds_mode="replay")
        freq = stream.frequency
        if freq <= 0:
            freq = random.randint(1, 50)  # assign a random frequency between 0 and 50
        dt = 1 / freq
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        attrs, data = collection.dataloader(self.config).read(stream.attrs)
        stream.attrs.update(attrs)

        # preprocessing
        logging.debug(f"index_cols={index_cols}, data.index={data.index.name}, data.columns={data.columns.values}")
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

        state = {}
        state["t0"] = None
        state["T0"] = None
        state["dt"] = dt
        state["data"] = data
        state["idx"] = 0
        state["index_cols"] = index_cols
        state["value_cols"] = value_cols
        return state

    def on_pull(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: dm.Queue,
        transform: Callable,
        state: dict,
        rate_limit: bool = True,
        strict_time: bool = True,
        use_relative_ts: bool = True,
    ) -> int | None:

        t0 = state["t0"]
        T0 = state["T0"]
        dt = state["dt"]
        data = state["data"]
        idx = state["idx"]
        index_cols = state["index_cols"]
        value_cols = state["value_cols"]

        # termination condition
        if idx == len(data.index):
            return 0

        # create record
        record = data.iloc[idx]
        index = {k: record[k] for k in index_cols}
        value = {k: record[k] for k in value_cols}

        # wait until time requirements are met
        if strict_time:
            if t0 is None or T0 is None:
                t0, T0 = time.perf_counter(), index[index_cols[0]]
                state["t0"] = t0
                state["T0"] = T0
            else:
                ti, Ti = time.perf_counter(), index[index_cols[0]]
                dt = (Ti - T0) - (ti - t0)
                if rate_limit and (dt > 0):
                    time.sleep(dt)
        elif rate_limit:
            time.sleep(dt)

        # postprocessing
        if use_relative_ts:
            index[index_cols[0]] -= T0

        # send record
        msg = dict(index=index, value=value)
        q.put(transform(msg))

        # increment pointer
        state["idx"] = idx + 1

    def on_detach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: dm.Queue,
        transform: Callable,
        state: dict,
    ) -> None:
        # termination indicator
        eof = dm.END_OF_STREAM
        q.put(transform(eof))
        self.logger.info(f"replay ended")

    def _serve_coro(
        self,
        source_id: str,
        stream_id: str,
        *,
        attrs: dict,
    ):
        import pylsl

        from .util import stream_to_stream_info

        collection = self.__collections[source_id]
        stream = collection.streams[stream_id]
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
