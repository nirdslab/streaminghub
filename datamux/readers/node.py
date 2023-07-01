import asyncio
import logging
from collections import OrderedDict
from typing import List

import pylsl
from dfds.typing import Stream

from serializers import Serializer

from . import Reader
from .util import create_stream_from_info

logger = logging.getLogger()


class NodeReader(Reader):
    """
    Stream Reader for DFDS Nodes

    """

    streams: List[Stream] = []

    def refresh_streams(
        self,
    ) -> None:
        self.streams.clear()
        stream_infos = pylsl.resolve_streams()
        for stream_info in stream_infos:
            stream = create_stream_from_info(stream_info)
            self.streams.append(stream)

    def list_streams(
        self,
    ) -> List[Stream]:
        return self.streams

    def create_query(
        self,
        stream: Stream,
    ) -> str:
        query_args = OrderedDict({})
        query_args["source_id"] = stream.name
        query_args["desc/stream/name"] = stream.name
        for k, v in stream.attrs.items():
            query_args[f"desc/attributes/{k}"] = v
        query_str = " and ".join([f"{k}='{v}'" for k, v in query_args.items()])
        return query_str

    def read(
        self,
        stream: Stream,
        queue: asyncio.Queue,
    ) -> asyncio.Task:
        serializer = Serializer(backend="json")

        query = self.create_query(stream)
        logger.debug("query: %s", query)

        # run one query to get a superset of the requested streams
        stream_infos = pylsl.resolve_bypred(query)
        logger.debug("found %d stream(s)", len(stream_infos))
        assert len(stream_infos) == 1
        stream_info = stream_infos[0]

        # create task to live-stream data
        inlet = pylsl.StreamInlet(stream_info, recover=False)
        return asyncio.create_task(self.relay_async(inlet, serializer, queue))

    async def relay_async(
        self,
        inlet: pylsl.StreamInlet,
        serializer: Serializer,
        queue: asyncio.Queue,
    ):
        logger.info("initializing live stream")
        s_info = create_stream_from_info(inlet.info())
        logger.info("started live stream")

        while True:
            # fetch data chunk
            try:
                (chunk, t) = inlet.pull_chunk(timeout=0.0)
            except pylsl.LostError as e:
                logger.info(f"LSL connection lost: {e}")
                break
            # process data chunk
            if chunk is None or len(chunk) == 0:
                await asyncio.sleep(1e-3)
            else:
                message = serializer.encode("data", stream=s_info, index=t, value=chunk)
                await queue.put(message)

        logger.info("ended live stream")
