import asyncio
from multiprocessing import Queue

from dfds.typing import Collection, Stream
from pydantic import BaseModel

from readers import CollectionReader, NodeReader
from util import gen_randseq

prefix = "d_"


class StreamAck(BaseModel):
    status: bool
    randseq: str | None = None


class DataMuxAPI:
    """
    API for DataMux.

    It provides three modes of execution.

    * **Listen** mode: read live data streams (LSL) on the local network.
    * **Replay** mode: replay datasets from storage to mimic a live data stream.
    * **Guided** mode: simulate random/guided data as a data stream.

    """

    def __init__(self):
        """
        Create API instance.

        """
        self.reader_n = NodeReader()
        self.reader_c = CollectionReader()

    def list_collections(
        self,
    ) -> list[Collection]:
        """
        List all collections.

        Returns:
            list[Collection]: list of available collections.
        """
        self.reader_c.refresh_collections()
        collections = self.reader_c.list_collections()
        return collections

    def list_collection_streams(
        self,
        collection_name: str,
    ) -> list[Stream]:
        """
        List all streams in a collection.

        Args:
            collection_name (str): name of collection.

        Returns:
            list[Stream]: list of streams in collection.
        """
        streams = self.reader_c.list_streams(collection_name)
        return streams

    def replay_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
        sink: Queue,
        transform=None,
    ) -> StreamAck:
        """
        Replay a collection-stream into a given queue.

        Args:
            collection_name (str): name of collection.
            stream_name (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to replay.
            sink (asyncio.Queue): destination to buffer replayed data.
            transform (Callable): optional transform to apply to each data point.

        Returns:
            StreamAck: status and reference information.
        """
        topic = prefix + gen_randseq()
        t = (lambda x: [topic.encode()] + transform(x)[1:]) if transform is not None else None
        self.reader_c.replay(collection_name, stream_name, attrs, sink, t)
        return StreamAck(status=True, randseq=topic)

    def publish_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
    ) -> StreamAck:
        """
        Publish a collection-stream as a LSL stream.

        Args:
            collection_name (str): name of collection.
            stream_name (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to publish.

        Returns:
            StreamAck: status and reference information.
        """
        self.reader_c.restream(collection_name, stream_name, attrs)
        return StreamAck(status=True)

    def list_live_streams(
        self,
    ) -> list[Stream]:
        """
        List all live streams.

        Returns:
            list[Stream]: list of available live streams.
        """
        self.reader_n.refresh_streams()
        streams = self.reader_n.list_streams()
        return streams

    def read_live_stream(
        self,
        stream_name: str,
        attrs: dict,
        sink: Queue,
        transform=None,
    ) -> StreamAck:
        """
        Read data from a live stream (LSL) into a given queue.

        Args:
            stream_name (str): name of live stream.
            attrs (dict): attributes specifying which live stream to read.
            sink (asyncio.Queue): destination to buffer replayed data.
            transform (Callable): optional transform to apply to each data point.

        Returns:
            StreamAck: status and reference information.
        """
        topic = prefix + gen_randseq()
        t = (lambda x: [topic.encode()] + transform(x)[1:]) if transform is not None else None
        self.reader_n.relay(stream_name, attrs, sink, t)
        return StreamAck(status=True, randseq=topic)
