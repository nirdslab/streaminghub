import abc
import multiprocessing

from threading import Thread

from streaminghub_pydfds.typing import Node, Stream


class Proxy(abc.ABC):
    """
    Base Class for DFDS Data Proxies (Role - Proxying Live Data)

    * list_nodes()

    * list_streams(node_id: str)

    * proxy(node_id, stream_id, queue)

    """

    @abc.abstractmethod
    def list_nodes(self) -> list[Node]: ...

    @abc.abstractmethod
    def list_streams(self, node_id: str) -> list[Stream]: ...

    @abc.abstractmethod
    def _proxy_coro(self, device_id: str, stream_id: str, q: multiprocessing.Queue) -> None: ...

    def proxy(
        self,
        device_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ):
        thread = Thread(None, self._proxy_coro, stream_id, (device_id, stream_id, q), daemon=True)
        thread.start()


from .empatica_e4 import EmpaticaE4Proxy
from .pupil_core import PupilCoreProxy
