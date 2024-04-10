#!/usr/bin/env python3
import codecs
import logging
import multiprocessing
import re
import socket

import streaminghub_pydfds as dfds
from rich.logging import RichHandler
from streaminghub_datamux.typing import Proxy
from streaminghub_pydfds.typing import Node, Stream


class E4ServerState:
    """
    Server States
    """

    NEW = "new"
    WAITING = "waiting"
    NO_DEVICES = "no_devices"
    DEVICES_FOUND = "devices_found"
    CONNECTED_TO_DEVICE = "connected"
    READY_TO_SUBSCRIBE = "ready_to_subscribe"
    SUBSCRIBE_COMPLETED = "subscribe completed"
    STREAMING = "streaming"


class E4SSCommand:
    """
    Server Commands
    """

    DEVICE_DISCOVER_LIST = "device_discover_list"
    DEVICE_CONNECT_BTLE = "device_connect_btle"
    DEVICE_DISCONNECT_BTLE = "device_disconnect_btle"
    DEVICE_LIST = "device_list"
    DEVICE_CONNECT = "device_connect"
    DEVICE_DISCONNECT = "device_disconnect"
    DEVICE_SUBSCRIBE = "device_subscribe"
    PAUSE = "pause"


class EmpaticaE4Proxy(Proxy):
    """
    Empatica E4 Proxy for Real-Time Data Streaming

    Dependencies: A [Running/Mock] E4 Streaming Server

    """

    buffer_size: int = 4096
    logger = logging.getLogger(__name__)
    nodes: list[Node] = []
    node_template: Node

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.config = dfds.load_config()
        fp = (self.config.meta_dir / "empatica_e4.node.json").as_posix()
        # get DFDS metadata for empatica e4
        self.node_template = dfds.Parser().get_node_metadata(fp)
        # initialize proxy
        self.server_state = E4ServerState.NEW
        self.patterns = [
            # (typ, cmd, arg, data)
            re.compile(
                r"^(?:(R)\s)?(device_discover_list|device_connect_btle|device_disconnect_btle|device_list|device_connect|device_disconnect|pause)(?:\s([\.\w]+))?(?:\s?(.+?))?$"
            ),
            # (typ, cmd, sid, arg, data)
            re.compile(r"^(?:(R)\s)?(device_subscribe)(?:\s(\w+))?(?:\s([\.\w]+))?(?:\s?(.+?))?$"),
            # (sid, time, data)
            re.compile(
                r"^(\w+)\s([\d.]+)\s?(.*)$",
            ),
        ]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def setup(self):
        self.sock.connect((socket.gethostname(), 28000))

    def encode(self, s_: str) -> bytes:
        return codecs.encode(s_ + "\r\n")

    def handle_outgoing_msgs(
        self,
        device_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ):
        if self.server_state == E4ServerState.NO_DEVICES:
            self.logger.debug("No devices found!")
            exit(1)
        elif self.server_state == E4ServerState.DEVICES_FOUND:
            # connect to device
            self.logger.debug("Connecting to device...")
            self.sock.send(self.encode("%s %s" % (E4SSCommand.DEVICE_CONNECT, device_id)))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.CONNECTED_TO_DEVICE:
            # pause streaming initially
            self.logger.debug("Initializing...")
            self.sock.send(self.encode("%s ON" % E4SSCommand.PAUSE))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.READY_TO_SUBSCRIBE:
            # subscribe to stream_id
            self.logger.debug("Subscribing to stream: %s" % stream_id)
            self.sock.send(self.encode("%s %s ON" % (E4SSCommand.DEVICE_SUBSCRIBE, stream_id)))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.SUBSCRIBE_COMPLETED:
            # begin streaming data
            self.logger.debug("Requesting data")
            self.sock.send(self.encode("%s OFF" % E4SSCommand.PAUSE))
            self.server_state = E4ServerState.STREAMING

    def handle_incoming_msgs(
        self,
        device_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ):
        # pull messages from socket
        buffer: str = codecs.decode(self.sock.recv(self.buffer_size))
        for message in filter(None, map(str.strip, buffer.split("\r\n"))):

            typ, cmd, sid, arg, data = self.parse_message(message)

            # Data Stream
            if typ == "" and self.server_state == E4ServerState.STREAMING:
                vals = [float(arg)] + list(map(float, data.split()))
                keys = ["t"] + list(range(len(vals) - 1))
                q.put_nowait(dict(zip(keys, vals)))

            # DEVICE_CONNECT response
            elif cmd == E4SSCommand.DEVICE_CONNECT:
                if arg == "ERR":
                    raise ValueError(f"Error connecting to device: {data}")
                elif arg == "OK":
                    self.logger.debug("Connected to device")
                    self.server_state = E4ServerState.CONNECTED_TO_DEVICE

            # PAUSE response
            elif cmd == E4SSCommand.PAUSE:
                if arg == "ERR":
                    raise ValueError(f"Error pausing streaming: {data}")
                elif arg == "ON":
                    self.logger.debug("Streaming on hold")
                    self.server_state = E4ServerState.READY_TO_SUBSCRIBE
                elif arg == "OFF":
                    self.logger.debug("Streaming started")
                    self.server_state = E4ServerState.STREAMING

            # DEVICE SUBSCRIBE response
            elif cmd == E4SSCommand.DEVICE_SUBSCRIBE:
                if arg == "ERR":
                    raise ValueError(f"Error subscribing to: {sid} - {data}")
                elif arg == "OK":
                    self.logger.debug(f"Subscribed to: {sid}")
                    self.server_state = E4ServerState.SUBSCRIBE_COMPLETED

            # default
            else:
                raise ValueError(f"Unknown message: {message}")

    def parse_message(self, message: str) -> tuple[str, str, str, str, str]:
        # parse message
        typ = cmd = sid = arg = data = str("")
        if (match := self.patterns[0].match(message)) is not None:
            (typ, cmd, arg, data) = match.groups()
        elif (match := self.patterns[1].match(message)) is not None:
            (typ, cmd, sid, arg, data) = match.groups()
        elif (match := self.patterns[2].match(message)) is not None:
            (sid, arg, data) = match.groups()
            sid = sid[3:].lower()  # drop E4_ prefix and lowercase
        else:
            raise ValueError(f"Unknown message: {message}")
        return typ, cmd, sid, arg, data

    def list_nodes(self) -> list[Node]:
        # request available nodes
        node_ids = []
        self.logger.debug("Getting available nodes...")
        self.sock.send(self.encode(E4SSCommand.DEVICE_LIST))
        self.server_state = E4ServerState.WAITING
        # DEVICE_LIST response
        buffer: str = codecs.decode(self.sock.recv(self.buffer_size))
        for message in filter(None, map(str.strip, buffer.split("\r\n"))):
            typ, cmd, sid, arg, data = self.parse_message(message)
            node_ids = [x.split()[0] for x in data.strip("| ").split("|")]
            n = len(node_ids)
            assert n == int(arg)
            self.logger.debug(f"nodes(s) found: {n}")
            if n == 0:
                self.server_state = E4ServerState.NO_DEVICES
            else:
                self.server_state = E4ServerState.DEVICES_FOUND
            self.nodes = [Node(**self.node_template.model_dump(exclude={"id"}), id=id) for id in node_ids]
        return self.nodes

    def list_streams(
        self,
        node_id: str,
    ) -> list[Stream]:
        node_ids = [node.id for node in self.nodes]
        assert node_id in node_ids
        return list(self.nodes[node_ids.index(node_id)].outputs.values())

    def _proxy_coro(
        self,
        device_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ) -> None:
        self.logger.debug(f"Started task for device={device_id}, stream: {stream_id}...")
        while True:
            try:
                self.handle_outgoing_msgs(device_id, stream_id, q)
                self.handle_incoming_msgs(device_id, stream_id, q)
            except KeyboardInterrupt:
                self.logger.debug(f"Interrupted task for device={device_id}, stream: {stream_id}...")
                break
        self.logger.debug(f"Ended task for device={device_id}, stream: {stream_id}...")


def main():
    proxy = EmpaticaE4Proxy()
    proxy.setup()
    nodes = proxy.list_nodes()
    print(nodes)
    assert len(nodes) > 0
    node = nodes[0]
    streams = proxy.list_streams(node.id)
    print(streams)
    assert len(streams) > 0
    stream = streams[0]
    # queue = multiprocessing.Queue()
    # proxy.proxy(node.id, stream.name, queue)

    # while True:
    #     item = queue.get()
    #     print(item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    main()
