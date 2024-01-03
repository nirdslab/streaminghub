#!/usr/bin/env python3
import codecs
import logging
import re
import socket

import dfds
import pylsl
from rich.logging import RichHandler

from . import Interface


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


class Connector(Interface):
    """
    Empatica E4 -> LSL Connector (via E4 Streaming Server)
    """

    buffer_size: int = 4096
    logger = logging.getLogger(__name__)

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.parser: dfds.Parser = dfds.Parser()
        self.node = self.parser.get_node_metadata("repository/empatica_e4.node.json")
        self.num_subs: int = 0
        self.device_id: str
        self.outlets: dict = {}
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

    def encode(self, s_: str) -> bytes:
        return codecs.encode(s_ + "\r\n")

    def get_outlet(self, stream_id: str) -> pylsl.StreamOutlet:
        self.outlets[stream_id] = self.outlets.get(
            stream_id,
            dfds.create_outlet(
                stream_id=stream_id,
                stream=self.node.outputs[stream_id],
            ),
        )
        return self.outlets[stream_id]

    def start(self):
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((socket.gethostname(), 28000))
        while True:
            self.handle_outgoing_msgs(sock)
            self.handle_incoming_msgs(sock)

    def handle_outgoing_msgs(
        self,
        s: socket.socket,
    ):
        if self.server_state == E4ServerState.NEW:
            # request devices list
            self.logger.debug("Getting list of devices...")
            s.send(self.encode(E4SSCommand.DEVICE_LIST))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.NO_DEVICES:
            self.logger.debug("No devices found!")
            exit(1)
        elif self.server_state == E4ServerState.DEVICES_FOUND:
            # connect to device
            self.logger.debug("Connecting to device...")
            s.send(self.encode("%s %s" % (E4SSCommand.DEVICE_CONNECT, self.device_id)))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.CONNECTED_TO_DEVICE:
            # pause streaming initially
            self.logger.debug("Initializing...")
            s.send(self.encode("%s ON" % E4SSCommand.PAUSE))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.READY_TO_SUBSCRIBE:
            # subscribe to streams
            stream = sorted(self.node.outputs)[self.num_subs]
            self.logger.debug("Subscribing to stream: %s" % stream)
            s.send(self.encode("%s %s ON" % (E4SSCommand.DEVICE_SUBSCRIBE, stream)))
            self.server_state = E4ServerState.WAITING
        elif self.server_state == E4ServerState.SUBSCRIBE_COMPLETED:
            # begin streaming data
            self.logger.debug("Requesting data")
            s.send(self.encode("%s OFF" % E4SSCommand.PAUSE))
            self.server_state = E4ServerState.STREAMING

    def handle_incoming_msgs(
        self,
        s: socket.socket,
    ):
        # pull messages from socket
        buffer: str = codecs.decode(s.recv(self.buffer_size))
        for message in [*map(str.strip, buffer.split("\r\n"))]:
            # parse message
            typ: str = ""
            cmd: str = ""
            sid: str = ""
            arg: str = ""
            data: str = ""
            if (match := self.patterns[0].match(message)) is not None:
                (typ, cmd, arg, data) = match.groups()
            elif (match := self.patterns[1].match(message)) is not None:
                (typ, cmd, sid, arg, data) = match.groups()
            elif (match := self.patterns[2].match(message)) is not None:
                (sid, arg, data) = match.groups()
                sid = sid[3:].lower()  # drop E4_ prefix and lowercase
            else:
                raise ValueError(f"Unknown message: {message}")

            # Data Stream
            if typ == "" and self.server_state == E4ServerState.STREAMING:
                outlet = self.get_outlet(sid)
                # only parse command if outlet has consumers
                if outlet.have_consumers():
                    outlet.push_sample([*map(float, data.split())] or [0], float(arg))

            # DEVICE_LIST response
            elif cmd == E4SSCommand.DEVICE_LIST:
                device_ids = [x.split()[0] for x in data.strip("| ").split("|")]
                num = len(device_ids)
                assert num == int(arg)
                self.logger.debug(f"device(s) found: {num}")

                if num == 0:
                    self.server_state = E4ServerState.NO_DEVICES
                    raise ValueError(f"No devices found: {num}")

                self.server_state = E4ServerState.DEVICES_FOUND

                # choose the only device
                if num == 1:
                    return device_ids[0]

                # prompt user to select device
                while True:
                    device_id = input(f"Enter device id: ")
                    if device_id in device_ids:
                        return device_id
                    self.logger.debug(f"Invalid device id: {device_id}")

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
                    self.num_subs += 1
                    if self.num_subs == len(self.node.outputs):
                        self.server_state = E4ServerState.SUBSCRIBE_COMPLETED
                    else:
                        self.server_state = E4ServerState.READY_TO_SUBSCRIBE

            # default
            else:
                raise ValueError(f"Unknown message: {message}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    connector = Connector()
    connector.start()
