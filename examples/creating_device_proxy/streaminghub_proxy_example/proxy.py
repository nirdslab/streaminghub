#!/usr/bin/env python
import logging
from pathlib import Path
from random import random
from typing import Callable

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds
from streaminghub_datamux.typing import Queue


class ExampleProxy(datamux.Reader[dfds.Node]):
    """
    An Example Proxy for Real-Time Data Streaming

    """

    logger = logging.getLogger(__name__)
    sub_port: int
    pub_port: int
    stream_ids = {
        "gaze_l": "gaze.3d.1",
        "gaze_r": "gaze.3d.0",
        "pupil_l": "pupil.1",
        "pupil_r": "pupil.0",
    }
    nodes: list[dfds.Node] = []
    node_template: dfds.Node

    def __init__(
        self,
    ) -> None:
        """
        Create a proxy, and initialize state variables
        """
        super().__init__()
        # save params
        self.config = dfds.load_config()
        # get DFDS metadata for pupil core
        fp = (Path(__file__).parent / "node.json").as_posix()
        self.node_template = dfds.Parser().get_node_metadata(fp)

    def setup(self):
        self._is_setup = True

    def on_attach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
    ) -> dict:
        assert stream_id in self.stream_ids
        self.logger.debug(f"Started task for source={source_id}, stream: {stream_id}...")
        return {}

    def on_pull(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
        state: dict,
        rate_limit: bool,
    ) -> int | None:
        _ = rate_limit # nothing to rate-limit in proxies
        topic = self.stream_ids[stream_id]
        try:
            # message content
            self._proxy_random_msg(topic, q, transform)
        except KeyboardInterrupt:
            self.logger.debug(f"Interrupted task for source={source_id}, stream: {stream_id}...")
            return 1

    def on_detach(
        self,
        source_id: str,
        stream_id: str,
        attrs: dict,
        q: Queue,
        transform: Callable,
        state: dict,
    ) -> None:
        self.logger.debug(f"Ended task for source={source_id}, stream: {stream_id}...")

    def _proxy_random_msg(
        self,
        topic: str,
        queue: datamux.Queue,
        transform: Callable,
    ) -> None:
        t = 0.0
        c = 0.0
        # left pupil diam
        if topic.startswith("pupil.1"):
            pupil_d = random()
            queue.put_nowait(transform({"pupil_l": dict(d=pupil_d, c=c, t=t)}))
        # right pupil diam
        if topic.startswith("pupil.0"):
            pupil_d = random()
            queue.put_nowait(transform({"pupil_r": dict(d=pupil_d, c=c, t=t)}))
        # left gaze pos
        if topic.startswith("gaze.3d.1"):
            gaze_x, gaze_y, gaze_z = random(), random(), random()
            queue.put_nowait(transform({"gaze_l": dict(x=gaze_x, y=gaze_y, z=gaze_z, c=c, t=t)}))
        # right gaze pos
        if topic.startswith("gaze.3d.0"):
            gaze_x, gaze_y, gaze_z = random(), random(), random()
            queue.put_nowait(transform({"gaze_r": dict(x=gaze_x, y=gaze_y, z=gaze_z, c=c, t=t)}))

    def list_sources(self) -> list[dfds.Node]:
        source_ids = ["1"]  # TODO fix this
        self.nodes = [dfds.Node(**self.node_template.model_dump(exclude={"id"}), id=id) for id in source_ids]
        return self.nodes

    def list_streams(self, source_id: str) -> list[dfds.Stream]:
        source_ids = [node.id for node in self.nodes]
        assert source_id in source_ids
        return list(self.nodes[source_ids.index(source_id)].outputs.values())
