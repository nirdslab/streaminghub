import abc
import logging
import multiprocessing.synchronize
import signal
from typing import Callable, Generic, TypeVar

import streaminghub_pydfds as dfds
from pydantic import BaseModel

END_OF_STREAM = {}  # NOTE do not change

Queue = multiprocessing.Queue
Flag = multiprocessing.synchronize.Event


def create_flag() -> Flag:
    return multiprocessing.Event()


class StreamAck(BaseModel):
    status: bool
    randseq: str | None = None


class IAttach(abc.ABC):
    """
    Base class with functions to listen to data streams via DataMux APIs

    Abstract Function(s):
    * on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
    * on_pull(source_id, stream_id, attrs, q, transform, state, **kwargs)
    * on_detach(source_id, stream_id, attrs, q, transform, state, **kwargs)

    Implemented Function(s):
    * attach(source_id, stream_id, attrs, q, transform, flag, **kwargs)

    """

    logger = logging.getLogger(__name__)

    def attach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
        flag: Flag,
        **kwargs,
    ):
        proc = multiprocessing.Process(
            None,
            self._attach_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id, attrs, q, transform, flag),
            kwargs,
            daemon=True,
        )
        proc.start()

    def _attach_coro(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
        flag: Flag,
        **kwargs,
    ):
        state = self.on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
        self.logger.debug("attached to stream")
        while not flag.is_set():
            retval = self.on_pull(source_id, stream_id, attrs, q, transform, state, **kwargs)
            if retval is not None:
                break
        self.on_detach(source_id, stream_id, attrs, q, transform, state, **kwargs)
        self.logger.debug("detached from stream")

    @abc.abstractmethod
    def on_attach(
        self, source_id: str, stream_id: str, attrs: dict, q: Queue, transform: Callable, **kwargs
    ) -> dict: ...

    @abc.abstractmethod
    def on_pull(
        self, source_id: str, stream_id: str, attrs: dict, q: Queue, transform: Callable, state: dict, **kwargs
    ) -> int | None: ...

    @abc.abstractmethod
    def on_detach(
        self, source_id: str, stream_id: str, attrs: dict, q: Queue, transform: Callable, state: dict, **kwargs
    ) -> None: ...


class IServe(abc.ABC):
    """
    Base class with functions to publish data streams onto external programs

    Abstract Function(s):
    * _serve_coro(source_id: str, stream_id: str, **kwargs)

    Implemented Function(s):
    * serve(source_id: str, stream_id: str, **kwargs)

    """

    logger = logging.getLogger(__name__)

    @abc.abstractmethod
    def _serve_coro(self, source_id: str, stream_id: str, **kwargs) -> None: ...

    def serve(
        self,
        source_id: str,
        stream_id: str,
        **kwargs,
    ):
        proc = multiprocessing.Process(
            None,
            self._serve_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id),
            kwargs,
            daemon=True,
        )
        proc.start()


T = TypeVar("T", dfds.Node, dfds.Collection)


class Reader(Generic[T], IAttach, abc.ABC):
    """
    Base class with functions to listen data from both live and stored sources

    Abstract Function(s):
    * setup(**kwargs)
    * list_sources()
    * list_streams(source_id)
    * on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
    * on_pull(source_id, stream_id, attrs, q, transform, state, **kwargs)
    * on_detach(source_id, stream_id, attrs, q, transform, state, **kwargs)

    Implemented Function(s):
    * attach(source_id, stream_id, attrs, q, transform, flag, **kwargs)

    """

    logger = logging.getLogger(__name__)
    _is_setup = False

    @property
    def is_setup(self):
        return self._is_setup

    @abc.abstractmethod
    def setup(self, **kwargs) -> None: ...

    @abc.abstractmethod
    def list_sources(self) -> list[T]: ...

    @abc.abstractmethod
    def list_streams(self, source_id: str) -> list[dfds.Stream]: ...


class ManagedTask:

    logger = logging.getLogger(__name__)
    proc: multiprocessing.Process

    def __init__(self, queue: Queue) -> None:
        self.name = self.__class__.__name__
        self.queue = queue
        self.flag = False

    def __signal__(self, *args) -> None:
        self.flag = True

    def __run__(self, *args, **kwargs) -> None:
        signal.signal(signal.SIGTERM, self.__signal__)
        while not self.flag:
            self.step(*args, **kwargs)

    def start(self, *args, **kwargs):
        self.proc = multiprocessing.Process(
            group=None,
            target=self.__run__,
            args=args,
            kwargs=kwargs,
            name=self.name,
            daemon=False,
        )
        self.proc.start()
        self.logger.info(f"Started {self.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        self.logger.info(f"Stopped {self.name}")

    @abc.abstractmethod
    def step(self, *args, **kwargs) -> None: ...


class IAPI(abc.ABC):

    @abc.abstractmethod
    def list_collections(self) -> list[dfds.Collection]:
        """
        List all collections.

        Returns:
            list[Collection]: list of available collections.
        """

    @abc.abstractmethod
    def list_collection_streams(self, collection_id: str) -> list[dfds.Stream]:
        """
        List all streams in a collection.

        Args:
            collection_id (str): name of collection.

        Returns:
            list[Stream]: list of streams in collection.
        """

    @abc.abstractmethod
    def replay_collection_stream(
        self, collection_id: str, stream_id: str, attrs: dict, sink: Queue, uid: bytes | None = None
    ) -> StreamAck:
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

    @abc.abstractmethod
    def stop_task(self, randseq: str) -> StreamAck: ...

    @abc.abstractmethod
    def publish_collection_stream(self, collection_id: str, stream_id: str, attrs: dict) -> StreamAck:
        """
        Publish a collection-stream as a LSL stream.

        Args:
            collection_id (str): name of collection.
            stream_id (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to publish.

        Returns:
            StreamAck: status and reference information.
        """

    @abc.abstractmethod
    def list_live_nodes(self) -> list[dfds.Node]:
        """
        List all live nodes.

        Returns:
            list[Node]: list of live nodes.
        """

    @abc.abstractmethod
    def list_live_streams(self, node_id: str) -> list[dfds.Stream]:
        """
        List all streams in a live node.

        Returns:
            list[Stream]: list of available live streams.
        """

    @abc.abstractmethod
    def proxy_live_stream(
        self, node_id: str, stream_id: str, attrs: dict, sink: Queue, uid: bytes | None = None
    ) -> StreamAck:
        """
        Proxy data from a live stream onto a given queue.

        Args:
            node_id (str): id of live node.
            stream_id (str): id of the live stream.
            attrs (dict): attributes specifying which live stream to read.
            sink (asyncio.Queue): destination to buffer replayed data.
            uid (Callable): optional uid to append to each data point.

        Returns:
            StreamAck: status and reference information.
        """
