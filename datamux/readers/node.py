import asyncio
import logging
from collections import OrderedDict
from typing import List

import pylsl
from dfds.typing import Stream

from . import Reader
from .util import stream_info_to_stream, stream_inlet_to_stream

logger = logging.getLogger()


class NodeReader(Reader):
    """
    Stream Reader for DFDS Nodes

    Functions Provided:

    * refresh_streams()

    * list_streams()

    * relay(stream_id, queue)

    """

    __streams: List[Stream] = []

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
    ) -> List[Stream]:
        return self.__streams

    def relay(
        self,
        stream_name: str,
        attrs: dict,
        randseq: str,
        queue: asyncio.Queue,
    ) -> asyncio.Task:
        stream = None
        for s in self.__streams:
            is_name_matched = s.name == stream_name
            is_attrs_matched = dict(s.attrs) == attrs
            if is_name_matched and is_attrs_matched:
                stream = s
        assert stream
        query = self.__create_query(stream)
        logger.info("query: %s", query)

        # get the LSL stream for the DFDS stream
        stream_infos = pylsl.resolve_bypred(query)
        logger.info("found %d stream(s)", len(stream_infos))
        assert len(stream_infos) == 1
        stream_info = stream_infos[0]

        # create task to live-stream data
        logger.info("creating inlet")
        inlet = pylsl.StreamInlet(stream_info)
        logger.info("creating relay task")
        return asyncio.create_task(self.__relay_coro(inlet, randseq, queue))

    def __create_query(
        self,
        stream: Stream,
    ) -> str:
        query_args = OrderedDict({})
        query_args["name"] = stream.name
        for k, v in stream.attrs.items():
            query_args[f"desc/attrs/{k}"] = v
        query_str = " and ".join([f"{k}='{v}'" for k, v in query_args.items()])
        return query_str

    async def __relay_coro(
        self,
        inlet: pylsl.StreamInlet,
        randseq: str,
        queue: asyncio.Queue,
    ):
        stream = stream_inlet_to_stream(inlet)
        if not "dfds_mode" in stream.attrs:
            stream.attrs.update(dfds_mode="relay")

        # column names
        index_cols = list(stream.index)
        value_cols = list(stream.fields)

        subtopic = randseq.encode()

        # relay each record
        logger.info("started relay")
        while True:
            try:
                (values, indices) = inlet.pull_chunk(timeout=0.0)
            except pylsl.LostError as e:
                logger.info(f"LSL connection lost: {e}")
                break
            if values is None or len(values) == 0:
                await asyncio.sleep(1e-3)
            else:
                for index, value in zip(indices, values):
                    # FIXME currently only supports 1D index
                    index_dict = {index_cols[0]: index}
                    value_dict = dict(zip(value_cols, value))
                    await queue.put((b"data_" + subtopic, dict(index=index_dict, value=value_dict)))
        logger.info("ended relay")
