import asyncio
import logging
from collections import OrderedDict
from typing import List

import pylsl
from dfds.typing import Stream

from serializers import Serializer

from . import Reader
from .util import stream_info_to_stream

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
        queue: asyncio.Queue,
    ) -> asyncio.Task:
        stream = [s for s in self.__streams if s.name == stream_name][0]
        serializer = Serializer(backend="json")

        query = self.__create_query(stream)
        logger.debug("query: %s", query)

        # get the LSL stream for the DFDS stream
        stream_infos = pylsl.resolve_bypred(query)
        logger.debug("found %d stream(s)", len(stream_infos))
        assert len(stream_infos) == 1
        stream_info = stream_infos[0]

        # create task to live-stream data
        inlet = pylsl.StreamInlet(stream_info, recover=False)
        return asyncio.create_task(self.__relay_coro(inlet, serializer, queue))

    def __create_query(
        self,
        stream: Stream,
    ) -> str:
        query_args = OrderedDict({})
        query_args["name"] = stream.name
        for k, v in stream.attrs.items():
            query_args[f"desc/{k}"] = v
        query_str = " and ".join([f"{k}='{v}'" for k, v in query_args.items()])
        return query_str

    async def __relay_coro(
        self,
        inlet: pylsl.StreamInlet,
        serializer: Serializer,
        queue: asyncio.Queue,
    ):
        stream = stream_info_to_stream(inlet.info())
        stream.attrs.update(dfds_mode="relay")

        # relay each record
        logger.info("started relay")
        while True:
            try:
                (chunk, t) = inlet.pull_chunk(timeout=0.0)
            except pylsl.LostError as e:
                logger.info(f"LSL connection lost: {e}")
                break
            if chunk is None or len(chunk) == 0:
                await asyncio.sleep(1e-3)
            else:
                message = serializer.encode("data", stream=stream, index=t, value=chunk)
                await queue.put(message)
        logger.info("ended relay")
