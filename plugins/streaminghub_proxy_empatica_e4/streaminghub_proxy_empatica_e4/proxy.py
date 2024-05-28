#!/usr/bin/env python3
import codecs
import logging
import multiprocessing
import re
import socket
from pathlib import Path

import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

from .util import E4ServerState, E4SSCommand


class EmpaticaE4Proxy(datamux.Reader[dfds.Node]):
    """
    Empatica E4 Proxy for Real-Time Data Streaming

    Dependencies: A [Running/Mock] E4 Streaming Server

    """

    buffer_size: int = 4096
    logger = logging.getLogger(__name__)
    sources: list[dfds.Node] = []
    source_template: dfds.Node

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.config = dfds.load_config()
        fp = (Path(__file__).parent / "node.json").as_posix()
        # get DFDS metadata for empatica e4
        self.source_template = dfds.Parser().get_node_metadata(fp)
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
        self._is_setup = True

    def encode(self, s_: str) -> bytes:
        return codecs.encode(s_ + "\r\n")

    def handle_outgoing_msgs(
        self,
        source_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ):
        if self.server_state == E4ServerState.NO_DEVICES:
            self.logger.debug("No devices found!")
            exit(1)
        elif self.server_state == E4ServerState.DEVICES_FOUND:
            # connect to device
            self.logger.debug("Connecting to device...")
            self.sock.send(self.encode("%s %s" % (E4SSCommand.DEVICE_CONNECT, source_id)))
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
        source_id: str,
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

    def list_sources(self) -> list[dfds.Node]:
        # request available sources
        source_ids = []
        self.logger.debug("Getting available sources...")
        self.sock.send(self.encode(E4SSCommand.DEVICE_LIST))
        self.server_state = E4ServerState.WAITING
        # DEVICE_LIST response
        buffer: str = codecs.decode(self.sock.recv(self.buffer_size))
        for message in filter(None, map(str.strip, buffer.split("\r\n"))):
            typ, cmd, sid, arg, data = self.parse_message(message)
            source_ids = [x.split()[0] for x in data.strip("| ").split("|")]
            n = len(source_ids)
            assert n == int(arg)
            self.logger.debug(f"source(s) found: {n}")
            if n == 0:
                self.server_state = E4ServerState.NO_DEVICES
            else:
                self.server_state = E4ServerState.DEVICES_FOUND
            self.sources = [dfds.Node(**self.source_template.model_dump(exclude={"id"}), id=id) for id in source_ids]
        return self.sources

    def list_streams(
        self,
        source_id: str,
    ) -> list[dfds.Stream]:
        source_ids = [node.id for node in self.sources]
        assert source_id in source_ids
        return list(self.sources[source_ids.index(source_id)].outputs.values())

    def _attach_coro(
        self,
        source_id: str,
        stream_id: str,
        q: multiprocessing.Queue,
    ) -> None:
        self.logger.debug(f"Started task for source={source_id}, stream: {stream_id}...")
        while True:
            try:
                self.handle_outgoing_msgs(source_id, stream_id, q)
                self.handle_incoming_msgs(source_id, stream_id, q)
            except KeyboardInterrupt:
                self.logger.debug(f"Interrupted task for source={source_id}, stream: {stream_id}...")
                break
        self.logger.debug(f"Ended task for source={source_id}, stream: {stream_id}...")
