import asyncio
import logging
from collections import defaultdict

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds
from streaminghub_datamux.rpc import create_rpc_client

from .topics import *


class DataMuxRemoteAPI:
    """
    Remote API for DataMux.

    It provides three modes of execution.

    * **Listen** mode: read live data streams (LSL) on the local network.
    * **Replay** mode: replay datasets from storage to mimic a live data stream.
    * **Guided** mode: simulate random/guided data as a data stream.

    """

    def __init__(
        self,
        rpc_name: str,
        codec_name: str,
    ) -> None:
        """
        Create Remote API instance.

        Args:
            rpc_name (str): method of RPC. supports {websocket, direct}.
            codec_name (str): name of codec. supports {json, avro}.
        """
        self.active = False
        # queues - sending
        self.outgoing = asyncio.Queue()
        # queues - receiving
        self.incoming = asyncio.Queue()
        # rpc module
        self.rpc = create_rpc_client(
            name=rpc_name,
            codec_name=codec_name,
            incoming=self.incoming,
            outgoing=self.outgoing,
        )
        # request handling module
        self.handlers: dict[bytes, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())
        self.logger = logging.getLogger(__name__)

    async def __handle_incoming__(
        self,
    ):
        while self.active:
            topic, content = await self.incoming.get()
            self.logger.debug(f"<: {topic}: {content}")
            await self.handlers[topic].put(content)

    async def __send_await__(
        self,
        topic: bytes,
        content: dict,
    ):
        self.logger.debug(f">: {topic}: {content}")
        await self.outgoing.put((topic, content))
        return self.handlers[topic]

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ):
        """
        Establish remote connection.

        Args:
            server_host (str): Hostname of running server
            server_port (int): Port of running server
        """
        self.active = True
        await self.rpc.connect(server_host, server_port)
        asyncio.create_task(self.__handle_incoming__())

    async def disconnect(
        self,
    ):
        """
        Close remote connection.

        """
        self.active = False

    async def list_collections(
        self,
    ) -> list[dfds.Collection]:
        """
        List all collections.

        Returns:
            list[Collection]: list of available collections.
        """
        topic = TOPIC_LIST_COLLECTIONS
        content: dict[str, str] = {}
        result = await self.__send_await__(topic, content)
        items = await result.get()
        collections = [dfds.Collection(**item) for item in items]
        return collections

    async def list_collection_streams(
        self,
        collection_id: str,
    ) -> list[dfds.Stream]:
        """
        List all streams in a collection.

        Args:
            collection_id (str): name of collection.

        Returns:
            list[Stream]: list of streams in collection.
        """
        topic = TOPIC_LIST_COLLECTION_STREAMS
        content = dict(collection_id=collection_id)
        result = await self.__send_await__(topic, content)
        items = await result.get()
        streams = [dfds.Stream(**item) for item in items]
        return streams

    async def replay_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict[str, str],
        sink: asyncio.Queue,
    ) -> datamux.StreamAck:
        """
        Replay a collection-stream into a given queue.

        Args:
            collection_id (str): name of collection.
            stream_id (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to replay.
            sink (asyncio.Queue): destination to buffer replayed data.

        Returns:
            StreamAck: status and reference information.
        """
        topic = TOPIC_REPLAY_COLLECTION_STREAM
        content = dict(
            collection_id=collection_id,
            stream_id=stream_id,
            attrs=attrs,
        )
        result = await self.__send_await__(topic, content)
        info = await result.get()
        ack = datamux.StreamAck(**info)
        assert ack.randseq is not None
        stream_topic = ack.randseq.encode()
        self.handlers[stream_topic] = sink
        return ack

    async def publish_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict[str, str],
    ) -> datamux.StreamAck:
        """
        Publish a collection-stream as a LSL stream.

        Args:
            collection_id (str): name of collection.
            stream_id (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to publish.

        Returns:
            StreamAck: status and reference information.
        """
        topic = TOPIC_PUBLISH_COLLECTION_STREAM
        content = dict(
            collection_id=collection_id,
            stream_id=stream_id,
            attrs=attrs,
        )
        result = await self.__send_await__(topic, content)
        info = await result.get()
        ack = datamux.StreamAck(**info)
        return ack

    async def stop_task(
        self,
        randseq: str,
    ) -> datamux.StreamAck:
        topic = TOPIC_STOP_TASK
        content = dict(randseq=randseq)
        result = await self.__send_await__(topic, content)
        info = await result.get()
        ack = datamux.StreamAck(**info)
        return ack

    async def list_live_streams(
        self,
        node_id: str,
    ) -> list[dfds.Stream]:
        """
        List all live streams.

        Returns:
            list[Stream]: list of available live streams.
        """
        topic = TOPIC_LIST_LIVE_STREAMS
        content: dict[str, str] = dict(node_id=node_id)
        result = await self.__send_await__(topic, content)
        items = await result.get()
        streams = [dfds.Stream(**item) for item in items]
        return streams

    async def proxy_live_stream(
        self,
        node_id: str,
        stream_id: str,
        attrs: dict,
        sink: asyncio.Queue,
    ) -> datamux.StreamAck:
        """
        Proxy data from a live stream onto a given queue.

        Args:
            node_id (str): id of live node.
            stream_id (str): id of the live stream.
            attrs (dict): attributes specifying which live stream to read.
            sink (asyncio.Queue): destination to buffer replayed data.

        Returns:
            StreamAck: status and reference information.
        """
        topic = TOPIC_READ_LIVE_STREAM
        content = dict(node_id=node_id, stream_id=stream_id, attrs=attrs)
        result = await self.__send_await__(topic, content)
        info = await result.get()
        ack = datamux.StreamAck(**info)
        assert ack.randseq is not None
        stream_topic = ack.randseq.encode()
        self.handlers[stream_topic] = sink
        return ack
