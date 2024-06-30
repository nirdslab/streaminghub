import logging

import pylsl
import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds
from typing import Callable

from .util import stream_info_to_stream, stream_inlet_to_stream


class LSLProxy(datamux.Reader[dfds.Node]):
    """
    LabStreamingLayer Proxy for Real-Time Data Streaming

    Dependencies: PyLSL + liblsl

    """

    __streams: list[dfds.Stream] = []
    logger = logging.getLogger(__name__)

    def _refresh_streams(
        self,
    ) -> None:
        self.__streams.clear()
        stream_infos = pylsl.resolve_streams()
        for stream_info in stream_infos:
            stream = stream_info_to_stream(stream_info)
            # at this point, stream.node is already set
            stream.attrs.update({"mode": "proxy"})
            self.__streams.append(stream)

    def __create_query(
        self,
        stream: dfds.Stream,
    ) -> str:
        query_args = {}
        query_args["name"] = stream.name
        for k, v in stream.attrs.items():
            query_args[f"desc/attrs/{k}"] = v
        query_str = " and ".join([f"{k}='{v}'" for k, v in query_args.items()])
        return query_str

    def setup(self) -> None:
        # nothing to set up here
        self._is_setup = True

    def list_sources(self) -> list[dfds.Node]:
        # no concept of node here. maybe use host/ip later?
        return [dfds.Node(id="lsl")]

    def list_streams(
        self,
        source_id: str,
    ) -> list[dfds.Stream]:
        assert source_id == "lsl"
        self._refresh_streams()
        return self.__streams

    def on_attach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: datamux.Queue,
        transform: Callable,
    ) -> dict:
        assert source_id == "lsl"
        stream = None
        for s in self.__streams:
            is_name_matched = s.name == stream_id
            is_attrs_matched = dict(s.attrs) == attrs
            if is_name_matched and is_attrs_matched:
                stream = s
        assert stream
        query = self.__create_query(stream)
        self.logger.info("query: %s", query)

        # get the LSL stream for the DFDS stream
        stream_infos = pylsl.resolve_bypred(query)
        self.logger.info("found %d stream(s)", len(stream_infos))
        assert len(stream_infos) == 1
        stream_info = stream_infos[0]

        # create task to live-stream data
        self.logger.info("creating inlet")
        inlet = pylsl.StreamInlet(stream_info)

        stream = stream_inlet_to_stream(inlet)
        if not "dfds_mode" in stream.attrs:
            stream.attrs.update(dfds_mode="relay")

        state = {}
        state["inlet"] = inlet
        state["stream"] = stream
        state["index_cols"] = list(stream.index)
        state["value_cols"] = list(stream.fields)
        return state

    def on_pull(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: datamux.Queue,
        transform: Callable,
        state: dict,
        rate_limit: bool = True,
        strict_time: bool = True,
        use_relative_ts: bool = True,
    ) -> int | None:
        _ = rate_limit, strict_time, use_relative_ts # nothing to rate-limit in proxies
        inlet = state["inlet"]
        index_cols = state["index_cols"]
        value_cols = state["value_cols"]
        try:
            (values, indices) = inlet.pull_chunk()
        except pylsl.LostError as e:
            self.logger.info(f"LSL connection lost: {e}")
            return 1
        if values is None or len(values) == 0:
            return
        else:
            for index, value in zip(indices, values):
                # FIXME currently only supports 1D index
                index_dict = {index_cols[0]: index}
                value_dict = dict(zip(value_cols, value))
                msg = dict(index=index_dict, value=value_dict)
                q.put(transform(msg))

    def on_detach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: datamux.Queue,
        transform: Callable,
        state: dict,
    ) -> None:
        inlet = state["inlet"]
        # termination indicator
        eof = datamux.END_OF_STREAM
        inlet.close_stream()
        q.put(transform(eof))
        self.logger.info("relay ended")
