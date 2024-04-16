import abc
import multiprocessing
from threading import Thread
from typing import Generic, TypeVar

import streaminghub_pydfds as dfds
from pydantic import BaseModel

END_OF_STREAM = {}  # NOTE do not change


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
    def _attach_coro(self, source_id: str, stream_id: str, q: multiprocessing.Queue, **kwargs) -> None: ...

    def attach(
        self,
        source_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
        **kwargs,
    ):
        thread = Thread(
            None,
            self._attach_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id, q),
            kwargs,
            daemon=True,
        )
        thread.start()


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
        thread = Thread(
            None,
            self._serve_coro,
            f"{source_id}_{stream_id}",
            (source_id, stream_id),
            kwargs,
            daemon=True,
        )
        thread.start()


T = TypeVar("T", dfds.Node, dfds.Collection)


class Reader(Generic[T], IAttach, abc.ABC):
    """
    Base class with functions to listen data from both live and stored sources

    Functions (Private):
    * _attach_coro(source_id, stream_id, q, **kwargs)

    Functions (Public):
    * attach(source_id, stream_id, q, **kwargs)
    * list_sources()
    * list_streams(source_id)

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
