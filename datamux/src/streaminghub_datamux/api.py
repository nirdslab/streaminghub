from multiprocessing import Queue
from threading import Event

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

from .managers import CollectionManager, ProxyManager
from .util import gen_randseq

prefix = "d_"


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
        self.config = dfds.load_config()
        self.proxy_n = ProxyManager()
        self.reader_c = CollectionManager(self.config)
        self.context: dict[str, Event] = {}

    def list_collections(
        self,
    ) -> list[dfds.Collection]:
        """
        List all collections.

        Returns:
            list[Collection]: list of available collections.
        """
        collections = self.reader_c.list_sources()
        return collections

    def list_collection_streams(
        self,
        collection_name: str,
    ) -> list[dfds.Stream]:
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
    ) -> datamux.StreamAck:
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
        randseq = prefix + gen_randseq()
        t = (lambda x: [randseq.encode(), *transform(x)]) if transform is not None else None
        self.context[randseq] = Event()
        self.reader_c.attach(collection_name, stream_name, sink, attrs=attrs, transform=t, flag=self.context[randseq])
        return datamux.StreamAck(status=True, randseq=randseq)

    def stop_task(
        self,
        randseq: str,
    ) -> datamux.StreamAck:
        if randseq in self.context:
            flag = self.context.pop(randseq)
            flag.set()
            return datamux.StreamAck(status=True)
        return datamux.StreamAck(status=True)

    def publish_collection_stream(
        self,
        collection_name: str,
        stream_name: str,
        attrs: dict,
    ) -> datamux.StreamAck:
        """
        Publish a collection-stream as a LSL stream.

        Args:
            collection_name (str): name of collection.
            stream_name (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to publish.

        Returns:
            StreamAck: status and reference information.
        """
        self.reader_c.serve(collection_name, stream_name, attrs=attrs)
        return datamux.StreamAck(status=True)

    def list_live_nodes(
        self,
    ) -> list[dfds.Node]:
        """
        List all live nodes.

        Returns:
            list[Node]: list of live nodes.
        """
        nodes = self.proxy_n.list_sources()
        return nodes

    def list_live_streams(
        self,
        node_id: str,
    ) -> list[dfds.Stream]:
        """
        List all streams in a live node.

        Returns:
            list[Stream]: list of available live streams.
        """
        streams = self.proxy_n.list_streams(node_id)
        return streams

    def proxy_live_stream(
        self,
        node_id: str,
        stream_id: str,
        attrs: dict,
        sink: Queue,
        transform=None,
    ) -> datamux.StreamAck:
        """
        Read data from a live stream (LSL) into a given queue.

        Args:
            node_id (str): id of live node.
            stream_id (str): id of the live stream.
            attrs (dict): attributes specifying which live stream to read.
            sink (asyncio.Queue): destination to buffer replayed data.
            transform (Callable): optional transform to apply to each data point.

        Returns:
            StreamAck: status and reference information.
        """
        randseq = prefix + gen_randseq()
        t = (lambda x: [randseq.encode(), *transform(x)]) if transform is not None else None
        self.context[randseq] = Event()
        self.proxy_n.attach(node_id, stream_id, sink, attrs=attrs, transform=t, flag=self.context[randseq])
        return datamux.StreamAck(status=True, randseq=randseq)
