from typing import Callable

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

from .managers import CollectionManager, ProxyManager


class API(datamux.IAPI):
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
        super().__init__()
        datamux.init_logging()
        self.config = dfds.load_config()
        self.reader_c = CollectionManager(self.config)
        self.proxy_n = ProxyManager()
        self.context: dict[str, datamux.Flag] = {}

        # setup CollectionManager
        self.reader_c.setup()

    def list_collections(
        self,
    ) -> list[dfds.Collection]:
        collections = self.reader_c.list_sources()
        return collections

    def list_collection_streams(
        self,
        collection_id: str,
    ) -> list[dfds.Stream]:
        streams = self.reader_c.list_streams(collection_id)
        return streams

    def replay_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict,
        sink: datamux.Queue,
        transform: Callable = datamux.identity,
        rate_limit: bool = True,
    ) -> datamux.StreamAck:
        randseq = datamux.prefix + datamux.gen_randseq()
        if isinstance(transform, datamux.Enveloper):
            transform.prefix = randseq.encode()
        self.context[randseq] = datamux.create_flag()
        self.reader_c.attach(
            source_id=collection_id,
            stream_id=stream_id,
            attrs=attrs,
            q=sink,
            transform=transform,
            flag=self.context[randseq],
            rate_limit=rate_limit,
        )
        return datamux.StreamAck(status=True, randseq=randseq)

    def publish_collection_stream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict,
    ) -> datamux.StreamAck:
        self.reader_c.serve(collection_id, stream_id, attrs=attrs)
        return datamux.StreamAck(status=True)

    def list_live_nodes(
        self,
    ) -> list[dfds.Node]:
        nodes = self.proxy_n.list_sources()
        return nodes

    def list_live_streams(
        self,
        node_id: str,
    ) -> list[dfds.Stream]:
        self.proxy_n.setup(proxy_id=node_id)
        streams = self.proxy_n.list_streams(node_id)
        return streams

    def proxy_live_stream(
        self,
        node_id: str,
        stream_id: str,
        attrs: dict,
        sink: datamux.Queue,
        transform: Callable = datamux.identity,
        rate_limit: bool = True,
    ) -> datamux.StreamAck:
        randseq = datamux.gen_randseq()
        self.context[randseq] = datamux.create_flag()
        self.proxy_n.setup(proxy_id=node_id)
        if isinstance(transform, datamux.Enveloper):
            transform.prefix = randseq.encode()
        self.proxy_n.attach(
            source_id=node_id,
            stream_id=stream_id,
            attrs=attrs,
            q=sink,
            transform=transform,
            flag=self.context[randseq],
            rate_limit=rate_limit,
        )
        return datamux.StreamAck(status=True, randseq=randseq)

    def stop_task(
        self,
        randseq: str,
    ) -> datamux.StreamAck:
        if randseq in self.context:
            flag = self.context.pop(randseq)
            flag.set()
        return datamux.StreamAck(status=True)

    def attach(
        self,
        stream: dfds.Stream,
        transform: Callable = datamux.identity,
        rate_limit: bool = True,

    ) -> datamux.SourceTask:
        mode = stream.attrs.get("mode")
        assert mode in ["proxy", "replay"]
        node = stream.node
        assert node is not None
        node_id = node.id
        stream_id = stream.attrs.get("id")
        assert stream_id is not None
        return datamux.APIStreamer(self, mode, node_id, stream_id, stream.attrs, transform, rate_limit=rate_limit)
