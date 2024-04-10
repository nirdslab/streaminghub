import logging
from multiprocessing import Queue
from threading import Event, Thread

import pylsl
import streaminghub_datamux.util as util
from streaminghub_datamux.typing import Reader
from streaminghub_pydfds.typing import Stream

from .util import stream_info_to_stream, stream_inlet_to_stream


class NodeReader(Reader):
    """
    Stream Reader for DFDS Nodes

    Functions Provided:

    * refresh_streams()

    * list_streams()

    * relay(stream_id, queue)

    """

    __streams: list[Stream] = []
    logger = logging.getLogger(__name__)

    def refresh_streams(
        self,
    ) -> None:
        self.__streams.clear()
        stream_infos = pylsl.resolve_streams()
        for stream_info in stream_infos:
            stream = stream_info_to_stream(stream_info)
            self.__streams.append(stream)

    def list_streams(
        self,
    ) -> list[Stream]:
        return self.__streams

    def relay(
        self,
        stream_name: str,
        attrs: dict,
        queue: Queue,
        transform,
        flag,
    ) -> None:
        stream = None
        for s in self.__streams:
            is_name_matched = s.name == stream_name
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
        thread = Thread(None, self.relay_coro, stream_name, (inlet, queue, transform, flag), daemon=True)
        thread.start()

    def __create_query(
        self,
        stream: Stream,
    ) -> str:
        query_args = {}
        query_args["name"] = stream.name
        for k, v in stream.attrs.items():
            query_args[f"desc/attrs/{k}"] = v
        query_str = " and ".join([f"{k}='{v}'" for k, v in query_args.items()])
        return query_str

    def relay_coro(
        self,
        inlet: pylsl.StreamInlet,
        queue: Queue,
        transform,
        flag: Event,
    ):
        stream = stream_inlet_to_stream(inlet)
        if not "dfds_mode" in stream.attrs:
            stream.attrs.update(dfds_mode="relay")

        # column names
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        # termination indicator
        eof = util.END_OF_STREAM
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
