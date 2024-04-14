import abc
import multiprocessing
from threading import Thread

import streaminghub_pydfds as dfds
from pydantic import BaseModel

END_OF_STREAM = {}  # NOTE do not change


class StreamAck(BaseModel):
    status: bool
    randseq: str | None = None


class Proxy(abc.ABC):
    """
    Base Class for DFDS Data Proxies (Role - Proxying Live Data)

    * setup()

    * list_nodes()

    * list_streams(node_id: str)

    * proxy(node_id, stream_id, queue)

    """

    @abc.abstractmethod
    def setup(self) -> None: ...

    @abc.abstractmethod
    def list_nodes(self) -> list[dfds.Node]: ...

    @abc.abstractmethod
    def list_streams(self, node_id: str) -> list[dfds.Stream]: ...

    @abc.abstractmethod
    def _proxy_coro(self, node_id: str, stream_id: str, q: multiprocessing.Queue, **kwargs) -> None: ...

    def proxy(
        self,
        node_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
        **kwargs,
    ):
        thread = Thread(
            None,
            self._proxy_coro,
            f"{node_id}_{stream_id}",
            (node_id, stream_id, q),
            kwargs,
            daemon=True,
        )
        thread.start()


class Reader:
    """
    Base Class for DFDS Data Readers (Role - Replaying Recorded Data)

    * list_collections()

    * list_streams(collection_id)

    * replay(collection_id, stream_id, attrs, queue)

    * restream(collection_id, stream_id, attrs)

    """

    @abc.abstractmethod
    def list_collections(self) -> list[dfds.Collection]: ...

    @abc.abstractmethod
    def list_streams(self, collection_id: str) -> list[dfds.Stream]: ...

    @abc.abstractmethod
    def _replay_coro(
        self, collection_id: str, stream_id: str, attrs: dict, q: multiprocessing.Queue, **kwargs
    ) -> None: ...

    @abc.abstractmethod
    def _restream_coro(self, collection_id: str, stream_id: str, attrs: dict, **kwargs) -> None: ...

    def replay(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict,
        q: multiprocessing.Queue,
        **kwargs,
    ):
        thread = Thread(
            None,
            self._replay_coro,
            f"{collection_id}_{stream_id}",
            (collection_id, stream_id, attrs, q),
            kwargs,
            daemon=True,
        )
        thread.start()

    def restream(
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict,
        **kwargs,
    ):
        thread = Thread(
            None,
            self._restream_coro,
            f"{collection_id}_{stream_id}",
            (collection_id, stream_id, attrs),
            kwargs,
            daemon=True,
        )
        thread.start()
