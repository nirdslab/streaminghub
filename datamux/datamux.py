import asyncio
from typing import Dict

from readers import CollectionReader, NodeReader


class DataMuxProtocol:
    def __init__(
        self,
        LIST_LIVE_STREAMS=b"list_live_streams",
        RELAY_LIVE_STREAM=b"relay_live_stream",
        LIST_COLLECTIONS=b"list_collections",
        LIST_COLLECTION_STREAMS=b"list_collection_streams",
        REPLAY_COLLECTION_STREAM=b"replay_collection_stream",
        RESTREAM_COLLECTION_STREAM=b"restream_collection_stream",
    ):
        self.LIST_LIVE_STREAMS = LIST_LIVE_STREAMS
        self.RELAY_LIVE_STREAM = RELAY_LIVE_STREAM
        self.LIST_COLLECTIONS = LIST_COLLECTIONS
        self.LIST_COLLECTION_STREAMS = LIST_COLLECTION_STREAMS
        self.REPLAY_COLLECTION_STREAM = REPLAY_COLLECTION_STREAM
        self.RESTREAM_COLLECTION_STREAM = RESTREAM_COLLECTION_STREAM


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
        protocol: DataMuxProtocol,
    ) -> None:
        self.reader_n = NodeReader()
        self.reader_c = CollectionReader()
        self.queue = asyncio.Queue()
        self.protocol = protocol

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
    ):
        """
        Relay data from a live stream

        """
        task = self.reader_n.relay(stream_name, attrs, self.queue)
        status = 0 if task.cancelled() else 1
        return dict(
            stream_name=stream_name,
            status=status,
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
    ):
        """
        Replay one stream in a collection directly.

        """
        task = self.reader_c.replay(collection_name, stream_name, attrs, self.queue)
        s = 0 if task.cancelled() else 1
        return dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=s,
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
        task = self.reader_c.restream(collection_name, stream_name, attrs)
        status = 0 if task.cancelled() else 1
        return dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
        )

    def process(
        self,
        topic: bytes,
        **content,
    ):
        """
        Handle Requests sent to DataMuxServer

        Args:
            topic (bytes): topic of the message
            content (dict): content of the message
        """

        # LIVE MODE (LSL -> Queue) =================================================================================================
        if topic == self.protocol.LIST_LIVE_STREAMS:
            retval = self.list_live_streams()
        elif topic == self.protocol.RELAY_LIVE_STREAM:
            retval = self.relay_live_streams(
                content["stream_name"],
                content["attrs"],
            )
        # REPLAY MODE (File -> Queue) ==============================================================================================
        elif topic == self.protocol.LIST_COLLECTIONS:
            retval = self.list_collections()
        elif topic == self.protocol.LIST_COLLECTION_STREAMS:
            retval = self.list_collection_streams(
                content["collection_name"],
            )
        elif topic == self.protocol.REPLAY_COLLECTION_STREAM:
            retval = self.replay_collection_stream(
                content["collection_name"],
                content["stream_name"],
                content["attrs"],
            )
        # RESTREAM MODE (File -> LSL) ==============================================================================================
        elif topic == self.protocol.RESTREAM_COLLECTION_STREAM:
            collection_name = content["collection_name"]
            stream_name = content["stream_name"]
            attrs = content["attrs"]
            retval = self.restream_collection_stream(
                collection_name,
                stream_name,
                attrs,
            )
        # FALLBACK =================================================================================================================
        else:
            retval = dict(error="Unknown Request")

        return self.queue.put((topic, retval))

    def deque(
        self,
    ):
        """
        Get the next pending message, if any

        """
        return self.queue.get()


class DataMuxClient:
    """
    Client to generate requests under the DataMux protocol

    """

    def __init__(
        self,
        protocol: DataMuxProtocol,
    ) -> None:
        self.protocol = protocol

    def list_live_streams(
        self,
    ):
        """
        List all live streams

        """
        topic = self.protocol.LIST_LIVE_STREAMS
        content: Dict[str, str] = {}
        return topic, content

    def relay_live_streams(
        self,
        stream_name: str,
        attrs: dict,
    ):
        """
        Relay data from a live stream

        """
        topic = self.protocol.RELAY_LIVE_STREAM
        content = dict(stream_name=stream_name, attrs=attrs)
        return topic, content

    def list_collections(
        self,
    ):
        """
        List all collections

        """
        topic = self.protocol.LIST_COLLECTIONS
        content: Dict[str, str] = {}
        return topic, content

    def list_collection_streams(
        self,
        collection_name: str,
    ):
        """
        List all streams in a collection

        """
        topic = self.protocol.LIST_COLLECTION_STREAMS
        content = dict(collection_name=collection_name)
        return topic, content

    def replay_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: Dict[str, str],
    ):
        """
        Replay one stream in a collection directly.

        """
        topic = self.protocol.REPLAY_COLLECTION_STREAM
        content = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        return topic, content

    def restream_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: Dict[str, str],
    ):
        """
        Replay one stream in a collection via LSL

        """
        topic = self.protocol.RESTREAM_COLLECTION_STREAM
        content = dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
        )
        return topic, content
