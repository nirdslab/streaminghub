import asyncio
import logging
from collections import defaultdict
from threading import Thread
from typing import Callable, Coroutine

import pickle
import base64
import streaminghub_datamux as dm
import streaminghub_pydfds as dfds
from streaminghub_datamux.rpc import create_rpc_client

from .topics import *


class AsyncExecutor(Thread):

    def __init__(self):
        super().__init__(daemon=True)
        self.logger = logging.getLogger(__name__)
        self.loop = asyncio.new_event_loop()
        self.outgoing = asyncio.Queue()
        self.incoming = asyncio.Queue()
        self.handlers: dict[bytes, dm.Queue] = defaultdict(lambda: dm.Queue())

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.__handle_incoming__())

    def submit(self, coro: Coroutine):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def __handle_incoming__(
        self,
    ):
        while True:
            topic, content = await self.incoming.get()
            self.logger.debug(f"<: {topic}: {content}")
            self.handlers[topic].put(content)

    def send(
        self,
        topic: bytes,
        content: dict,
    ) -> dm.Queue:
        self.logger.debug(f">: {topic}: {content}")
        self.submit(self.outgoing.put((topic, content))).result()
        return self.handlers[topic]


class RemoteAPI(dm.IAPI):
    """
    Remote API for dm.

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
        self.executor = AsyncExecutor()
        # rpc module
        self.rpc = create_rpc_client(
            name=rpc_name,
            codec_name=codec_name,
            incoming=self.executor.incoming,
            outgoing=self.executor.outgoing,
        )
        self.logger = logging.getLogger(__name__)

    def connect(
        self,
        server_host: str,
        server_port: int,
    ) -> None:
        """
        Establish remote connection.

        Args:
            server_host (str): Hostname of running server
            server_port (int): Port of running server
        """
        self.active = True
        self.executor.start()
        self.executor.submit(self.rpc.connect(server_host, server_port)).result()

    def disconnect(
        self,
    ) -> None:
        """
        Close remote connection.

        """
        self.active = False

    def list_collections(
        self,
    ) -> list[dfds.Collection]:
        topic = TOPIC_LIST_COLLECTIONS
        content: dict[str, str] = {}
        items = self.executor.send(topic, content).get()
        assert items is not None
        collections = [dfds.Collection(**item) for item in items]
        return collections

    def list_collection_streams(
        self,
        collection_id: str,
    ) -> list[dfds.Stream]:
        topic = TOPIC_LIST_COLLECTION_STREAMS
        content = dict(collection_id=collection_id)
        items = self.executor.send(topic, content).get()
        assert items is not None
        streams = [dfds.Stream(**item) for item in items]
        return streams

    def replay_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict[str, str],
        sink: dm.Queue,
        transform: Callable = dm.identity,
        rate_limit: bool = True,
        strict_time: bool = True,
        use_relative_ts: bool = True,
    ) -> dm.StreamAck:
        topic = TOPIC_REPLAY_COLLECTION_STREAM
        content = dict(
            collection_id=collection_id,
            stream_id=stream_id,
            attrs=attrs,
            transform=base64.b64encode(pickle.dumps(transform)),
            rate_limit=rate_limit,
            strict_time=strict_time,
            use_relative_ts=use_relative_ts,
        )
        info = self.executor.send(topic, content).get()
        assert info is not None
        ack = dm.StreamAck(**info)
        assert ack.randseq is not None
        stream_topic = ack.randseq.encode()
        self.executor.handlers[stream_topic] = sink
        return ack

    def publish_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict[str, str],
    ) -> dm.StreamAck:
        topic = TOPIC_PUBLISH_COLLECTION_STREAM
        content = dict(
            collection_id=collection_id,
            stream_id=stream_id,
            attrs=attrs,
        )
        info = self.executor.send(topic, content).get()
        assert info is not None
        ack = dm.StreamAck(**info)
        return ack

    def list_live_nodes(
        self,
    ) -> list[dfds.Node]:
        topic = TOPIC_LIST_LIVE_NODES
        content: dict[str, str] = {}
        items = self.executor.send(topic, content).get()
        assert items is not None
        nodes = [dfds.Node(**item) for item in items]
        return nodes

    def list_live_streams(
        self,
        node_id: str,
    ) -> list[dfds.Stream]:
        topic = TOPIC_LIST_LIVE_STREAMS
        content: dict[str, str] = dict(node_id=node_id)
        items = self.executor.send(topic, content).get()
        assert items is not None
        streams = [dfds.Stream(**item) for item in items]
        return streams

    def proxy_live_stream(
        self,
        node_id: str,
        stream_id: str,
        attrs: dict,
        sink: dm.Queue,
        transform: Callable = dm.identity,
        rate_limit: bool = True,
        strict_time: bool = True,
        use_relative_ts: bool = True,
    ) -> dm.StreamAck:
        topic = TOPIC_READ_LIVE_STREAM
        content = dict(
            node_id=node_id,
            stream_id=stream_id,
            attrs=attrs,
            transform=base64.b64encode(pickle.dumps(transform)),
            rate_limit=rate_limit,
            strict_time=strict_time,
            use_relative_ts=use_relative_ts,
        )
        info = self.executor.send(topic, content).get()
        assert info is not None
        ack = dm.StreamAck(**info)
        assert ack.randseq is not None
        stream_topic = ack.randseq.encode()
        self.executor.handlers[stream_topic] = sink
        return ack

    def stop_task(
        self,
        randseq: str,
    ) -> dm.StreamAck:
        topic = TOPIC_STOP_TASK
        content = dict(randseq=randseq)
        info = self.executor.send(topic, content).get()
        assert info is not None
        ack = dm.StreamAck(**info)
        return ack

    def attach(
        self,
        stream: dfds.Stream,
        transform: Callable = dm.identity,
        rate_limit: bool = True,
        strict_time: bool = True,
        use_relative_ts: bool = True,
    ) -> dm.SourceTask:
        mode = stream.attrs.get("mode")
        assert mode in ["proxy", "replay"]
        node = stream.node
        assert node is not None
        node_id = node.id
        stream_id = stream.attrs.get("id")
        assert stream_id is not None
        return dm.APIStreamer(
            self,
            mode,
            node_id,
            stream_id,
            stream.attrs,
            transform,
            rate_limit=rate_limit,
            strict_time=strict_time,
            use_relative_ts=use_relative_ts,
        )
