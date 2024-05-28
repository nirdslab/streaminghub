import logging
from multiprocessing import Queue
from threading import Event

import pylsl
import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

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

    def _attach_coro(
        self,
        source_id: str,
        stream_id: str,
        queue: Queue,
        *,
        transform,
        flag: Event,
        attrs: dict = {},
    ):
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
        self.logger.info("creating relay task")

        stream = stream_inlet_to_stream(inlet)
        if not "dfds_mode" in stream.attrs:
            stream.attrs.update(dfds_mode="relay")

        # column names
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        # termination indicator
        eof = datamux.END_OF_STREAM
        if transform is not None:
            eof = transform(eof)

        # relay each record
        self.logger.info("relay started")
        while True:
            if flag.is_set():
                self.logger.info(f"relay stop requested")
                break

            try:
                (values, indices) = inlet.pull_chunk()
            except pylsl.LostError as e:
                self.logger.info(f"LSL connection lost: {e}")
                break
            if values is None or len(values) == 0:
                pass
            else:
                for index, value in zip(indices, values):
                    # FIXME currently only supports 1D index
                    index_dict = {index_cols[0]: index}
                    value_dict = dict(zip(value_cols, value))
                    msg = dict(index=index_dict, value=value_dict)
                    if transform is not None:
                        msg = transform(msg)
                    queue.put_nowait(msg)

        inlet.close_stream()
        queue.put_nowait(eof)
        self.logger.info("relay ended")
