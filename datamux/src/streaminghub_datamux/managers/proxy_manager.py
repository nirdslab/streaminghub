import multiprocessing
from importlib.metadata import entry_points

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds


class ProxyManager(datamux.Proxy):
    """
    An interface to find any active nodes (bio-sensors),
    request their streams, and proxy their data.

    """

    def __init__(self) -> None:
        super().__init__()

        # find all entrypoints with group=streaminghub_datamux.proxy
        self.proxies: dict[str, datamux.Proxy] = {}
        for ep in entry_points(group="streaminghub_datamux.proxy"):
            cls = ep.load()
            if issubclass(cls, datamux.Proxy):
                self.proxies[ep.name] = cls()
                print(f"Loaded proxy: {ep.name}")
            else:
                print(f"Invalid proxy: {ep.name}")

        self.nodes: list[dfds.Node] = []
        self.node_ref: list[str] = []
        self.prox_ref: list[str] = []

    def setup(self) -> None:
        for prox in self.proxies.values():
            prox.setup()

    def list_nodes(self) -> list[dfds.Node]:
        # generate node id - proxy map
        self.nodes.clear()
        self.node_ref.clear()
        self.prox_ref.clear()
        for prox_name, prox in self.proxies.items():
            nodes = prox.list_nodes()
            self.nodes.extend(nodes)
            self.node_ref.extend([n.id for n in nodes])
            self.prox_ref.extend([prox_name] * len(nodes))
        return self.nodes

    def list_streams(self, node_id: str) -> list[dfds.Stream]:
        assert node_id in self.node_ref
        node_ref = self.node_ref.index(node_id)
        prox_ref = self.prox_ref.__getitem__(node_ref)
        node, prox = self.nodes[node_ref], self.proxies[prox_ref]
        return prox.list_streams(node_id)

    def _proxy_coro(self, node_id: str, stream_id: str, q: multiprocessing.Queue, **kwargs) -> None:
        assert node_id in self.node_ref
        node_ref = self.node_ref.index(node_id)
        prox_ref = self.prox_ref.__getitem__(node_ref)
        prox = self.proxies[prox_ref]
        return prox._proxy_coro(node_id, stream_id, q, **kwargs)
