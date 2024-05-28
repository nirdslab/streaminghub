#!/usr/bin/env python
import io
import logging
import multiprocessing
from pathlib import Path

import msgpack
import numpy as np
import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds
import zmq
from PIL import Image


class PupilCoreProxy(datamux.Reader[dfds.Node]):
    """
    Pupil Core Proxy for Real-Time Data Streaming

    Dependencies: A [Running/Mock] Pupil Labs Remote API

    """

    logger = logging.getLogger(__name__)
    sub_port: int
    pub_port: int
    stream_ids = {
        "world": "frame.world",
        "eye_l": "frame.eye.1",
        "eye_r": "frame.eye.0",
        "gaze_l": "gaze.3d.1",
        "gaze_r": "gaze.3d.0",
        "pupil_l": "pupil.1",
        "pupil_r": "pupil.0",
    }
    nodes: list[dfds.Node] = []
    node_template: dfds.Node
    ctx: zmq.Context
    ctrl_sock: zmq.Socket

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
        self.ctrl_ip = pupil_remote_ip
        self.ctrl_port = pupil_remote_port
        # get DFDS metadata for pupil core
        fp = (Path(__file__).parent / "node.json").as_posix()
        self.node_template = dfds.Parser().get_node_metadata(fp)
        # initialize proxy
        self.ctx = zmq.Context()
        self.ctrl_sock = self.ctx.socket(zmq.REQ)

    def setup(self):
        conn_str = f"tcp://{self.ctrl_ip}:{self.ctrl_port}"
        self.logger.debug(f"Getting PUB_PORT and SUB_PORT from {conn_str}...")
        self.ctrl_sock.connect(conn_str)
        self.ctrl_sock.send_string("SUB_PORT")
        self.sub_port = int(self.ctrl_sock.recv_string())
        self.ctrl_sock.send_string("PUB_PORT")
        self.pub_port = int(self.ctrl_sock.recv_string())
        self.logger.debug(f"Received SUB_PORT={self.sub_port}, PUB_PORT={self.pub_port}")
        self._is_setup = True

    def send_sock_opts(self, sock: zmq.Socket, opt: int, topic: str):
        sock.setsockopt_string(opt, topic)
        self.logger.debug(f"set opt={opt}, topic={topic}")

    def _attach_coro(
        self,
        source_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ) -> None:
        conn_str = f"tcp://{self.ctrl_ip}:{self.sub_port}"
        assert stream_id in self.stream_ids
        sock = self.ctx.socket(zmq.SUB)
        sock.connect(conn_str)
        self.logger.debug(f"Started task for source={source_id}, stream: {stream_id}...")
        stream_topic = self.stream_ids[stream_id]
        self.send_sock_opts(sock, zmq.SUBSCRIBE, stream_topic)
        while True:
            try:
                # receive raw data (bytes)
                [topic, msg, *extra] = sock.recv_multipart()
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
                self.logger.debug(f"Interrupted task for source={source_id}, stream: {stream_id}...")
                break
        self.send_sock_opts(sock, zmq.UNSUBSCRIBE, stream_topic)
        sock.disconnect(conn_str)
        sock.close()
        self.logger.debug(f"Ended task for source={source_id}, stream: {stream_id}...")

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
                pupil_d = message["diameter"]
                queue.put_nowait({"pupil_l": dict(d=pupil_d, c=c, t=t)})
            # right pupil diam
            if topic.startswith("pupil.0"):
                pupil_d = message["diameter"]
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

    def list_sources(self) -> list[dfds.Node]:
        source_ids = ["1"]  # TODO fix this
        self.nodes = [dfds.Node(**self.node_template.model_dump(exclude={"id"}), id=id) for id in source_ids]
        return self.nodes

    def list_streams(self, source_id: str) -> list[dfds.Stream]:
        source_ids = [node.id for node in self.nodes]
        assert source_id in source_ids
        return list(self.nodes[source_ids.index(source_id)].outputs.values())
