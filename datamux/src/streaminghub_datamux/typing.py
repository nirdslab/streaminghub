import abc
import multiprocessing.synchronize
import signal
from typing import Generic, TypeVar

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

    Functions (Private):
    * _attach_coro(source_id, stream_id, q, **kwargs)

    Functions (Public):
    * attach(source_id, stream_id, q, **kwargs)

    """

    @abc.abstractmethod
    def _attach_coro(self, source_id: str, stream_id: str, q: Queue, **kwargs) -> None: ...

    def attach(
        self,
        source_id: str,
        stream_id: str,
        q: Queue,
        **kwargs,
    ):
        proc = multiprocessing.Process(
            None,
            self._attach_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id, q),
            kwargs,
            daemon=True,
        )
        proc.start()


class IServe(abc.ABC):
    """
    Base class with functions to publish data streams onto external programs

    Functions (Private):
    * _serve_coro(source_id: str, stream_id: str, **kwargs)

    Functions (Public):
    * serve(source_id: str, stream_id: str, **kwargs)

    """

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

    Functions (Private):
    * _attach_coro(source_id, stream_id, q, **kwargs)

    Functions (Public):
    * setup(**kwargs)
    * list_sources()
    * list_streams(source_id)
    * attach(source_id, stream_id, q, **kwargs)

    """

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
        print(f"Started {self.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        print(f"Stopped {self.name}")

    @abc.abstractmethod
    def step(self, *args, **kwargs) -> None:
        raise NotImplementedError()
