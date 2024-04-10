import multiprocessing

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds


class MultiProxy(datamux.Proxy):
    """
    An interface to find any active nodes (bio-sensors),
    request their streams, and proxy their data.

    """

    def __init__(self) -> None:
        super().__init__()

        # TODO make this part dynamic
        from .empatica_e4 import EmpaticaE4Proxy
        from .pupil_core import PupilCoreProxy
        from .lsl import LSLProxy

        self.proxies: list[datamux.Proxy] = [
            EmpaticaE4Proxy(),
            PupilCoreProxy(),
            LSLProxy(),
        ]
        self.node_ref: list[dfds.Node] = []
        self.prox_ref: list[datamux.Proxy] = []

    def setup(self) -> None:
        for proxy in self.proxies:
            proxy.setup()

    def list_nodes(self) -> list[dfds.Node]:
        # generate node id - proxy map
        self.node_ref.clear()
        self.prox_ref.clear()
        for prox in self.proxies:
            nodes = prox.list_nodes()
            self.node_ref.extend(nodes)
            self.prox_ref.extend([prox] * len(nodes))
        return self.node_ref

    def list_streams(self, node_id: str) -> list[dfds.Stream]:
        node_ids = [n.id for n in self.node_ref]
        assert node_id in node_ids
        prox = self.prox_ref[node_ids.index(node_id)]
        return prox.list_streams(node_id)

    def _proxy_coro(self, node_id: str, stream_id: str, q: multiprocessing.Queue, **kwargs) -> None:
        node_ids = [n.id for n in self.node_ref]
        assert node_id in node_ids
        prox = self.prox_ref[node_ids.index(node_id)]
        return prox._proxy_coro(node_id, stream_id, q, **kwargs)
