from __future__ import annotations

import abc
import logging
import multiprocessing
import multiprocessing.synchronize
import signal
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel

import streaminghub_pydfds as dfds

from . import util as datamux

END_OF_STREAM = {}  # NOTE do not change
Q = multiprocessing.Queue

Flag = multiprocessing.synchronize.Event

D = TypeVar("D")


class Queue(Generic[D]):

    q: Q

    def __init__(self, empty: bool = False, timeout=None) -> None:
        super().__init__()
        self.timeout = timeout
        if empty:
            self.q = None  # type: ignore
        else:
            self.q = Q()

    def assign(self, q: Queue):
        self.q = q.q

    def get(self) -> D | None:
        try:
            return self.q.get(timeout=self.timeout)
        except:
            return None

    def put(self, obj: D, block: bool = True, timeout: float | None = None) -> None:
        return self.q.put(obj, block, timeout)

    def put_nowait(self, obj: D) -> None:
        return self.q.put_nowait(obj)


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
    * on_pull(source_id, stream_id, attrs, q, transform, state, rate_limit, **kwargs)
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
        rate_limit: bool = True,
        **kwargs,
    ):
        proc = multiprocessing.Process(
            None,
            self._attach_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id, attrs, q, transform, flag, rate_limit),
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
        rate_limit: bool = True,
        **kwargs,
    ):
        signal.signal(signal.SIGINT, lambda *_: flag.set())
        signal.signal(signal.SIGTERM, lambda *_: flag.set())
        datamux.init_logging()
        state = self.on_attach(source_id, stream_id, attrs, q, transform, **kwargs)
        self.logger.debug("attached to stream")
        while not flag.is_set():
            retval = self.on_pull(source_id, stream_id, attrs, q, transform, state, rate_limit, **kwargs)
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
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
        state: dict,
        rate_limit: bool,
        **kwargs,
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
    * on_pull(source_id, stream_id, attrs, q, transform, state, rate_limit, **kwargs)
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


class ITask(abc.ABC):

    logger = logging.getLogger(__name__)
    proc: multiprocessing.Process

    def __init__(self) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.flag = False

    def __signal__(self, *args) -> None:
        self.flag = True

    def __run__(self, *args, **kwargs) -> None:
        signal.signal(signal.SIGINT, self.__signal__)
        signal.signal(signal.SIGTERM, self.__signal__)
        datamux.init_logging()
        while not self.flag:
            try:
                retval = self(*args, **kwargs)
                if retval is not None:
                    self.logger.info(f"[{self.name}] returned with code: {retval}")
                    break
            except BaseException as e:
                self.logger.warn(f"[{self.name}] has crashed: {e}")

    def start(self, *args, **kwargs):
        self.proc = multiprocessing.Process(
            group=None,
            target=self.__run__,
            args=args,
            kwargs=kwargs,
            name=self.name,
            daemon=True,
        )
        self.proc.start()
        self.logger.info(f"Started {self.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        self.logger.info(f"Stopped {self.name}")

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> int | None: ...


class ITaskWithSource(ITask):
    source: Queue

    def __init__(self) -> None:
        super().__init__()


class SourceTask(ITaskWithSource):
    def __init__(self, transform=None) -> None:
        super().__init__()
        self.source = Queue(timeout=0.001)
        self.transform = transform


class PipeTask(ITaskWithSource):
    target: Queue

    def __init__(self, transform=None) -> None:
        super().__init__()
        self.source = Queue(timeout=0.001, empty=True)
        self.target = Queue(timeout=0.001)
        self.transform = transform


class SinkTask(ITaskWithSource):

    completed = create_flag()

    def __init__(self) -> None:
        super().__init__()
        self.source = Queue(timeout=0.001, empty=True)


class Pipeline(ITask):

    target: Queue

    @property
    def source(self) -> Queue:
        return self.tasks[0].source

    def __init__(self, *tasks: SourceTask | SinkTask | PipeTask | Pipeline) -> None:
        super().__init__()
        self.tasks = tasks
        for i, task in enumerate(self.tasks):
            if isinstance(task, SourceTask):
                assert i == 0
                q = task.source
                self.logger.debug(f"task={task.name}, source={task.source}")
            elif isinstance(task, SinkTask):
                assert i == len(self.tasks) - 1
                task.source = q
                self.completed = task.completed
                self.logger.debug(f"task={task.name}, source={task.source}")
            elif isinstance(task, PipeTask):
                if i == 0:
                    # source is empty
                    task.source = Queue(empty=True)
                    q = task.target
                    self.logger.debug(f"task={task.name}, source={task.source}, target={task.target}")
                else:
                    # source is non-empty
                    task.source = q
                    q = task.target
                    self.logger.debug(f"task={task.name}, source={task.source}, target={task.target}")
            elif isinstance(task, Pipeline):
                assert i > 0
                # source is non-empty
                assert q is not None
                task.source.assign(q)
                q = task.target
                self.logger.info(f"task={task.name}, source={task.source}, target={task.target}")
        self.target = q

    def start(self):
        for task in self.tasks:
            task.start()

    def stop(self):
        for task in self.tasks:
            task.stop()

    def run(self, duration: float | None = None):
        self.start()
        try:
            self.completed.wait(duration)
            self.logger.info("pipeline completed")
        except:
            self.logger.info("pipeline timed out")
        self.stop()

    def __call__(self, *args, **kwargs) -> None:
        raise ValueError("should never be called")


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
        self,
        collection_id: str,
        stream_id: str,
        attrs: dict,
        sink: Queue,
        transform: Callable = datamux.identity,
        rate_limit: bool = True,
    ) -> StreamAck:
        """
        Replay a collection-stream into a given queue.

        Args:
            collection_id (str): name of collection.
            stream_id (str): name of stream in collection.
            attrs (dict): attributes specifying which recording to replay.
            sink (asyncio.Queue): destination to buffer replayed data.
            transform (Callable): optional function to apply on each measurement.
            rate_limit (bool): optional switch to turn rate limiting on/off.

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
        self,
        node_id: str,
        stream_id: str,
        attrs: dict,
        sink: Queue,
        transform: Callable = datamux.identity,
        rate_limit: bool = True,
    ) -> StreamAck:
        """
        Proxy data from a live stream onto a given queue.

        Args:
            node_id (str): id of live node.
            stream_id (str): id of the live stream.
            attrs (dict): attributes specifying which live stream to read.
            sink (asyncio.Queue): destination to buffer replayed data.
            transform (Callable): optional function to apply on each measurement.
            rate_limit (bool): optional switch to turn rate limiting on/off.

        Returns:
            StreamAck: status and reference information.
        """

    @abc.abstractmethod
    def attach(
        self,
        stream: dfds.Stream,
    ) -> SourceTask:
        """
        Create task to get data from the given stream

        Args:
            stream (str): stream to attach onto
        Returns:
            SourceTask: a task that queues data between task.start() and task.stop() invocations
        """


class APIStreamer(SourceTask):

    task_id: str | None = None

    def __init__(
        self, api: IAPI, mode: str, node_id: str, stream_id: str, attrs: dict, transform: Callable, rate_limit: bool
    ) -> None:
        super().__init__()
        self.api = api
        self.mode = mode
        self.node_id = node_id
        self.stream_id = stream_id
        self.attrs = attrs
        self.source = Queue(timeout=0.001)
        self.transform = transform
        self.rate_limit = rate_limit

    def start(self, *args, **kwargs):
        if self.mode == "proxy":
            ack = self.api.proxy_live_stream(
                self.node_id, self.stream_id, self.attrs, self.source, self.transform, self.rate_limit
            )
            assert ack.randseq is not None
            self.task_id = ack.randseq
        elif self.mode == "replay":
            ack = self.api.replay_collection_stream(
                self.node_id,
                self.stream_id,
                self.attrs,
                self.source,
                self.transform,
                self.rate_limit,
            )
            assert ack.randseq is not None
            self.task_id = ack.randseq
        else:
            raise ValueError()

    def stop(self):
        assert self.task_id is not None
        ack = self.api.stop_task(self.task_id)
        assert ack.status == True

    def __call__(self, *args, **kwargs) -> None:
        raise ValueError("should never happen")
