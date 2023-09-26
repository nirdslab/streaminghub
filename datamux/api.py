import asyncio
import random

from readers import CollectionReader, NodeReader


def gen_randseq(length: int = 5):
    options = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    return "".join(random.choice(options) for x in range(length))


class DataMuxAPI:
    """
    API for DataMux

    It provides three modes of execution.

    * **Proxy** mode: proxy live LSL data streams on the local network
    * **Replay** mode: replay datasets from storage to mimic a live data stream
    * **Simulate** mode: simulate random/guided data as a data stream

    """

    def __init__(self):
        self.reader_n = NodeReader()
        self.reader_c = CollectionReader()

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
        randseq = gen_randseq()
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
        randseq = gen_randseq()
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
        randseq = gen_randseq()
        task = self.reader_c.restream(collection_name, stream_name, attrs, randseq)
        status = 0 if task.cancelled() else 1
        return dict(
            collection_name=collection_name,
            stream_name=stream_name,
            attrs=attrs,
            status=status,
            randseq=randseq,
        )
