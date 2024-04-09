#!/usr/bin/env python
import io
import logging
import multiprocessing
from threading import Thread

import msgpack
import numpy as np
import streaminghub_pydfds as dfds
import zmq
from PIL import Image
from rich.logging import RichHandler
from streaminghub_pydfds.typing import Node, Stream

from . import Proxy


class PupilCoreProxy(Proxy):
    """
    Pupil Core Proxy for Real-Time Data Streaming

    Dependencies: A [Running/Mock] Pupil Labs Remote API

    """

    logger = logging.getLogger(__name__)
    sub_port: int
    pub_port: int
    topics: list[str] = [
        "frame.",  # camera stream {world, eye0, eye1}
        "gaze.",  # gaze position data
        "pupil.",  # pupil data
        # "fixations",  # fixation data
        # 'notify',    # notifications
    ]
    is_setup: bool = False
    nodes: list[Node] = []
    node_template: Node

    def __init__(
        self,
        pupil_remote_ip: str = "localhost",
        pupil_remote_port: int = 50020,
    ) -> None:
        """
        Create a proxy which points to an active pupil remote

        Args:
            pupil_remote_ip (str): ip of running pupil remote
            pupil_remote_port (int): port of running pupil remote
        """
        super().__init__()
        # save params
        self.config = dfds.load_config()
        self.pupil_remote_ip = pupil_remote_ip
        self.pupil_remote_port = pupil_remote_port
        # get DFDS metadata for pupil core
        fp = (self.config.meta_dir / "pupil_core.node.json").as_posix()
        self.node_template = dfds.Parser().get_node_metadata(fp)
        # initialize proxy
        self.ctx = zmq.Context()
        self.pupil_remote_sock = self.ctx.socket(zmq.REQ)
        self.pupil_pub_sock = self.ctx.socket(zmq.PUB)
        self.pupil_sub_sock = self.ctx.socket(zmq.SUB)

    def setup(
        self,
    ) -> None:
        conn_str = f"tcp://{self.pupil_remote_ip}:{self.pupil_remote_port}"
        self.logger.debug(f"Connecting to Pupil Remote: {conn_str}...")
        self.pupil_remote_sock.connect(conn_str)
        self.logger.debug(f"Connected to Pupil Remote: {conn_str}")

        self.logger.debug("Requesting SUB_PORT and PUB_PORT...")
        self.pupil_remote_sock.send_string("SUB_PORT")
        self.sub_port = int(self.pupil_remote_sock.recv_string())
        self.pupil_remote_sock.send_string("PUB_PORT")
        self.pub_port = int(self.pupil_remote_sock.recv_string())
        self.logger.debug(f"Received SUB_PORT={self.sub_port}, PUB_PORT={self.pub_port}")

    def send_sock_opts(self, sock_opt: int):
        # subscribe to topics
        for sub_id in self.topics:
            self.pupil_sub_sock.setsockopt_string(sock_opt, sub_id)
            self.logger.debug(f"set opt={sock_opt} for topic={sub_id}")

    def _proxy_coro(
        self,
        node_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ) -> None:
        conn_str = f"tcp://{self.pupil_remote_ip}:{self.sub_port}"
        self.pupil_sub_sock.connect(conn_str)
        self.logger.debug(f"Started task for device={node_id}, stream: {stream_id}...")
        self.send_sock_opts(zmq.SUBSCRIBE)
        while True:
            try:
                # receive raw data (bytes)
                [topic, msg, *extra] = self.pupil_sub_sock.recv_multipart()
                topic = topic.decode()
                # message content
                payload: dict | None = None
                if len(msg) > 0:
                    d = msgpack.loads(msg)
                    assert isinstance(d, dict)
                    payload = d
                # frames
                frame: np.ndarray | None = None
                if len(extra) > 0:
                    frame = np.asarray(Image.open(io.BytesIO(extra[0])).convert("RGB"))
                self._proxy_msg(topic, payload, frame, q)
            except KeyboardInterrupt:
                self.logger.debug(f"Interrupted task for device={node_id}, stream: {stream_id}...")
                break
        self.send_sock_opts(zmq.UNSUBSCRIBE)
        self.pupil_sub_sock.disconnect(conn_str)
        self.logger.debug(f"Ended task for device={node_id}, stream: {stream_id}...")

    def _proxy_msg(
        self,
        topic: str,
        message: dict | None,
        frame: np.ndarray | None,
        queue: multiprocessing.Queue,
    ) -> None:
        t = 0.0
        c = 0.0
        if message is not None:
            t = message.get("timestamp", 0.0)
            c = message.get("confidence", 0.0)
            # left pupil diam
            if topic.startswith("pupil.1"):
                pupil_d = message["diameter_3d"]
                queue.put_nowait({"pupil_l": dict(d=pupil_d, c=c, t=t)})
            # right pupil diam
            if topic.startswith("pupil.0"):
                pupil_d = message["diameter_3d"]
                queue.put_nowait({"pupil_r": dict(d=pupil_d, c=c, t=t)})
            # left gaze pos
            if topic.startswith("gaze.3d.1"):
                gaze_x, gaze_y, gaze_z = message["gaze_point_3d"]
                queue.put_nowait({"gaze_l": dict(x=gaze_x, y=gaze_y, z=gaze_z, c=c, t=t)})
            # right gaze pos
            if topic.startswith("gaze.3d.0"):
                gaze_x, gaze_y, gaze_z = message["gaze_point_3d"]
                queue.put_nowait({"gaze_r": dict(x=gaze_x, y=gaze_y, z=gaze_z, c=c, t=t)})
        if frame is not None:
            # world frame
            if topic.startswith("frame.world"):
                assert frame is not None
                queue.put_nowait({"world": dict(frame=frame, t=t)})
            # left eye frame
            if topic.startswith("frame.eye.1"):
                assert frame is not None
                queue.put_nowait({"eye_l": dict(frame=frame, t=t)})
            # right eye frame
            if topic.startswith("frame.eye.0"):
                assert frame is not None
                queue.put_nowait({"eye_r": dict(frame=frame, t=t)})

    def list_nodes(self) -> list[Node]:
        if not self.is_setup:
            self.setup()
            self.is_setup = True
        node_ids = []  # TODO fix this
        self.nodes = [Node(id=id, **self.node_template.model_dump()) for id in node_ids]
        return self.nodes

    def list_streams(self, node_id: str) -> list[Stream]:
        node_ids = [node.id for node in self.nodes]
        assert node_id in node_ids
        return list(self.nodes[node_ids.index(node_id)].outputs.values())


def main():
    proxy = PupilCoreProxy()
    nodes = proxy.list_nodes()
    assert len(nodes) > 0
    node = nodes[0]
    streams = proxy.list_streams(node.id)
    assert len(streams) > 0
    stream = streams[0]
    queue = multiprocessing.Queue()
    proxy.proxy(node.id, stream.name, queue)

    while True:
        item = queue.get()
        print(item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    main()
