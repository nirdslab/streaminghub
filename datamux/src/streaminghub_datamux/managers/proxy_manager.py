from importlib.metadata import entry_points

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds


class ProxyManager(datamux.Reader[dfds.Node]):
    """
    An interface to find any active nodes (bio-sensors),
    request their streams, and proxy their data.

    Terminology
    ===========
    Proxy: May provide one or more nodes (referred by proxy_id)
    Node: A single bio-sensor device (referred by source_id)
    Stream: Each node provides one or more streams (referred by stream_id)

    """

    def __init__(self) -> None:
        super().__init__()
        # find all entrypoints with group=streaminghub_datamux.proxy
        self.proxies: dict[str, datamux.Reader[dfds.Node]] = {}
        for ep in entry_points(group="streaminghub_datamux.proxy"):
            cls = ep.load()
            if issubclass(cls, datamux.Reader):
                self.proxies[ep.name] = cls()
                print(f"Loaded proxy: {ep.name}")
            else:
                print(f"Invalid proxy: {ep.name}")
        self.nodes: list[dfds.Node] = []
        self.node_ref: list[str] = []
        self.prox_ref: list[str] = []

    def list_proxies(self) -> dict[str, datamux.Reader[dfds.Node]]:
        return self.proxies

    def setup(self, *, proxy_id: str) -> None:
        """
        Call setup() on a proxy

        Args:
            proxy_id (str): ID of the proxy to run setup() on
        """
        assert proxy_id in self.proxies
        prox = self.proxies[proxy_id]
        prox.setup()

    def list_sources(self) -> list[dfds.Node]:
        """
        List all nodes available on the set-up proxies

        Returns:
            list[dfds.Node]: List of available nodes
        """
        self.nodes.clear()
        self.node_ref.clear()
        self.prox_ref.clear()
        for prox_name, prox in self.proxies.items():
            if not prox.is_setup:
                continue
            nodes = prox.list_sources()
            self.nodes.extend(nodes)
            self.node_ref.extend([n.id for n in nodes])
            self.prox_ref.extend([prox_name] * len(nodes))
        return self.nodes

    def _resolve_prox_by_source_id(self, source_id: str):
        assert source_id in self.node_ref
        node_ref = self.node_ref.index(source_id)
        prox_ref = self.prox_ref.__getitem__(node_ref)
        return self.proxies[prox_ref]

    def list_streams(self, source_id: str) -> list[dfds.Stream]:
        prox = self._resolve_prox_by_source_id(source_id)
        return prox.list_streams(source_id)

    def _attach_coro(self, source_id: str, stream_id: str, q: datamux.Queue, **kwargs) -> None:
        prox = self._resolve_prox_by_source_id(source_id)
        return prox._attach_coro(source_id, stream_id, q, **kwargs)
