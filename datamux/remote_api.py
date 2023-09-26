import asyncio
import logging
from collections import defaultdict

from dfds.typing import Collection, Stream

from codec import create_codec
from remote_topics import *
from rpc import create_rpc_client


class DataMuxRemoteAPI:
    """
    Remote API for DataMux

    """

    def __init__(
        self,
        rpc_backend: str,
        serialization_backend: str,
    ) -> None:
        self.active = False
        # queues - sending
        self.codec_send_source = asyncio.Queue()
        self.rpc_send_source = self.codec_send_sink = asyncio.Queue()
        # queues - receiving
        self.codec_recv_source = self.rpc_recv_sink = asyncio.Queue()
        self.codec_recv_sink = asyncio.Queue()
        # rpc module
        self.rpc = create_rpc_client(
            name=rpc_backend,
            send_source=self.rpc_send_source,
            recv_sink=self.rpc_recv_sink,
        )
        # codec module
        self.codec = create_codec(
            backend=serialization_backend,
            send_source=self.codec_send_source,
            send_sink=self.codec_send_sink,
            recv_source=self.codec_recv_source,
            recv_sink=self.codec_recv_sink,
        )
        # request handling module
        self.handlers: dict[bytes, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())
        self.logger = logging.getLogger(__name__)

    async def __handle_incoming__(
        self,
    ):
        while self.active:
            topic, content = await self.codec_recv_sink.get()
            self.logger.debug(topic, content)
            await self.handlers[topic].put(content)

    async def __send_await__(
        self,
        topic: bytes,
        content: dict,
    ):
        await self.codec_send_source.put((topic, content))
        return self.handlers[topic]

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ):
        self.active = True
        await self.rpc.connect(server_host, server_port)
        asyncio.create_task(self.__handle_incoming__())

    async def list_live_streams(
        self,
    ) -> list[Stream]:
        """
        List all live streams

        """
        topic = TOPIC_LIST_LIVE_STREAMS
        content: dict[str, str] = {}
        qresult = await self.__send_await__(topic, content)
        self.logger.debug(qresult)
        streams = await qresult.get()
        return streams

    async def relay_live_streams(
        self,
        stream_name: str,
        attrs: dict,
    ) -> asyncio.Queue:
        """
        Relay data from a live stream

        """
        topic = TOPIC_RELAY_LIVE_STREAM
        content = dict(stream_name=stream_name, attrs=attrs)
        qstream = await self.__send_await__(topic, content)
        return qstream

    async def list_collections(
        self,
    ) -> list[Collection]:
        """
        List all collections

        """
        topic = TOPIC_LIST_COLLECTIONS
        content: dict[str, str] = {}
        qresult = await self.__send_await__(topic, content)
        collections = await qresult.get()
        return collections

    async def list_collection_streams(
        self,
        collection_name: str,
    ) -> list[Stream]:
        """
        List all streams in a collection

        """
        topic = TOPIC_LIST_COLLECTION_STREAMS
        content = dict(collection_name=collection_name)
        qresult = await self.__send_await__(topic, content)
        streams = await qresult.get()
        return streams

    async def replay_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict[str, str],
    ) -> asyncio.Queue:
        """
        Replay one stream in a collection directly.

        """
        topic = TOPIC_REPLAY_COLLECTION_STREAM
        query = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        qstream = await self.__send_await__(topic, query)
        return qstream

    async def restream_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict[str, str],
    ) -> dict:
        """
        Replay one stream in a collection via LSL

        """
        topic = TOPIC_RESTREAM_COLLECTION_STREAM
        content = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        qresult = await self.__send_await__(topic, content)
        info = await qresult.get()
        return info
