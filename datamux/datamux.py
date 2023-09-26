import asyncio
from collections import defaultdict
import random
from typing import Any, Dict

from dfds.typing import Collection, Stream

from codec import Codec
from readers import CollectionReader, NodeReader
from rpc import create_rpc_client, create_rpc_server


class Topics:
    LIST_LIVE_STREAMS: bytes = b"list_live_streams"
    RELAY_LIVE_STREAM: bytes = b"relay_live_stream"
    LIST_COLLECTIONS: bytes = b"list_collections"
    LIST_COLLECTION_STREAMS: bytes = b"list_collection_streams"
    REPLAY_COLLECTION_STREAM: bytes = b"replay_collection_stream"
    RESTREAM_COLLECTION_STREAM: bytes = b"restream_collection_stream"


class DataMuxServerAPI:
    def __init__(self):
        self.reader_n = NodeReader()
        self.reader_c = CollectionReader()

    def __gen_randseq(self, length: int = 5):
        options = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        return "".join(random.choice(options) for x in range(length))

    def list_live_streams(
        self,
    ):
        """
        List all live streams

        """
        self.reader_n.refresh_streams()
        streams = self.reader_n.list_streams()
        return dict(
            streams=[s.model_dump() for s in streams],
        )

    def relay_live_streams(
        self,
        stream_name: str,
        attrs: dict,
        sink: asyncio.Queue,
    ):
        """
        Relay data from a live stream

        """
        randseq = self.__gen_randseq()
        task = self.reader_n.relay(stream_name, attrs, randseq, sink)
        status = 0 if task.cancelled() else 1
        return dict(
            stream_name=stream_name,
            status=status,
            randseq=randseq,
        )

    def list_collections(
        self,
    ):
        """
        List all collections

        """
        self.reader_c.refresh_collections()
        collections = self.reader_c.list_collections()
        return dict(
            collections=[c.model_dump() for c in collections],
        )

    def list_collection_streams(
        self,
        collection_name: str,
    ):
        """
        List all streams in a collection

        """
        streams = self.reader_c.list_streams(collection_name)
        return dict(
            collection_name=collection_name,
            streams=[s.model_dump() for s in streams],
        )

    def replay_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
        sink: asyncio.Queue,
    ):
        """
        Replay one stream in a collection directly.

        """
        randseq = self.__gen_randseq()
        task = self.reader_c.replay(collection_name, stream_name, attrs, randseq, sink)
        status = 0 if task.cancelled() else 1
        return dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
            randseq=randseq,
        )

    def restream_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
    ):
        """
        Replay one stream in a collection via LSL

        """
        randseq = self.__gen_randseq()
        task = self.reader_c.restream(collection_name, stream_name, attrs, randseq)
        status = 0 if task.cancelled() else 1
        return dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
            randseq=randseq,
        )


class DataMuxServer:
    """
    Main Class for DataMux Functionality

    It provides three modes of execution.

    * **Proxy** mode: proxy live LSL data streams on the local network
    * **Replay** mode: replay datasets from storage to mimic a live data stream
    * **Simulate** mode: simulate random/guided data as a data stream

    """

    def __init__(
        self,
        rpc_backend: str,
        serialization_backend: str,
    ) -> None:
        self.active = False
        # queues - sending
        self.codec_send_source = self.api_send_sink = asyncio.Queue()
        self.rpc_send_source = self.codec_send_sink = asyncio.Queue()
        # queues - receiving
        self.codec_recv_source = self.rpc_recv_sink = asyncio.Queue()
        self.api_recv_source = self.codec_recv_sink = asyncio.Queue()
        # rpc module
        self.rpc = create_rpc_server(
            name=rpc_backend,
            send_source=self.rpc_send_source,
            recv_sink=self.rpc_recv_sink,
        )
        # codec module
        self.codec = Codec.with_backend(
            backend=serialization_backend,
            send_source=self.codec_send_source,
            send_sink=self.codec_send_sink,
            recv_source=self.codec_recv_source,
            recv_sink=self.codec_recv_sink,
        )
        # api module
        self.api = DataMuxServerAPI()

    async def __start(
        self,
    ):
        """
        Handle Requests sent to DataMuxServer

        Args:
            topic (bytes): topic of the message
            content (dict): content of the message
        """

        while self.active:
            topic, content = await self.api_recv_source.get()
            # LIVE MODE (LSL -> Queue) =================================================================================================
            if topic == Topics.LIST_LIVE_STREAMS:
                retval = self.api.list_live_streams()
            elif topic == Topics.RELAY_LIVE_STREAM:
                retval = self.api.relay_live_streams(
                    content["stream_name"],
                    content["attrs"],
                    self.api_send_sink,
                )
            # REPLAY MODE (File -> Queue) ==============================================================================================
            elif topic == Topics.LIST_COLLECTIONS:
                retval = self.api.list_collections()
            elif topic == Topics.LIST_COLLECTION_STREAMS:
                retval = self.api.list_collection_streams(
                    content["collection_name"],
                )
            elif topic == Topics.REPLAY_COLLECTION_STREAM:
                retval = self.api.replay_collection_stream(
                    content["collection_name"],
                    content["stream_name"],
                    content["attrs"],
                    self.api_send_sink,
                )
            # RESTREAM MODE (File -> LSL) ==============================================================================================
            elif topic == Topics.RESTREAM_COLLECTION_STREAM:
                collection_name = content["collection_name"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                retval = self.api.restream_collection_stream(
                    collection_name,
                    stream_name,
                    attrs,
                )
            # FALLBACK =================================================================================================================
            else:
                retval = dict(error="Unknown Request")

            return self.api_send_sink.put(retval)

    async def start(
        self,
        host: str,
        port: int,
    ):
        self.codec.start()
        asyncio.create_task(self.__start())
        asyncio.create_task(self.rpc.start(host, port))
        flag = asyncio.Future()
        await flag

    async def stop(
        self,
    ):
        await self.rpc.stop()
        self.codec.stop()


class DataMuxClientAPI:
    """
    Client to generate requests under the DataMux protocol

    """

    def __init__(
        self,
        rpc_backend: str,
        serialization_backend: str,
    ) -> None:
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
        self.codec = Codec.with_backend(
            backend=serialization_backend,
            send_source=self.codec_send_source,
            send_sink=self.codec_send_sink,
            recv_source=self.codec_recv_source,
            recv_sink=self.codec_recv_sink,
        )
        # request handling module
        self.handlers: dict[bytes, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())

    async def recv_loop(
        self,
    ):
        while True:
            topic, content = await self.codec_recv_sink.get()
            self.handlers[topic].put_nowait(content)

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ):
        await self.rpc.connect(server_host, server_port)
        asyncio.create_task(self.recv_loop())

    async def send_and_await_response(
        self,
        topic: bytes,
        content: dict,
    ):
        await self.codec_send_source.put((topic, content))
        return await self.handlers[topic].get()

    async def list_live_streams(
        self,
    ) -> list[Stream]:
        """
        List all live streams

        """
        topic = Topics.LIST_LIVE_STREAMS
        content: Dict[str, str] = {}
        return await self.send_and_await_response(topic, content)

    async def relay_live_streams(
        self,
        stream_name: str,
        attrs: dict,
    ):
        """
        Relay data from a live stream

        """
        topic = Topics.RELAY_LIVE_STREAM
        content = dict(stream_name=stream_name, attrs=attrs)
        return await self.send_and_await_response(topic, content)

    async def list_collections(
        self,
    ) -> list[Collection]:
        """
        List all collections

        """
        topic = Topics.LIST_COLLECTIONS
        content: Dict[str, str] = {}
        return await self.send_and_await_response(topic, content)

    async def list_collection_streams(
        self,
        collection_name: str,
    ) -> list[Stream]:
        """
        List all streams in a collection

        """
        topic = Topics.LIST_COLLECTION_STREAMS
        content = dict(collection_name=collection_name)
        return await self.send_and_await_response(topic, content)

    async def replay_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: Dict[str, str],
    ):
        """
        Replay one stream in a collection directly.

        """
        topic = Topics.REPLAY_COLLECTION_STREAM
        content = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        return await self.send_and_await_response(topic, content)

    async def restream_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: Dict[str, str],
    ):
        """
        Replay one stream in a collection via LSL

        """
        topic = Topics.RESTREAM_COLLECTION_STREAM
        content = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        return await self.send_and_await_response(topic, content)
