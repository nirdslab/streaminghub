#!/usr/bin/env python3
import codecs
import os
import socket
from typing import List

from pylsl import StreamOutlet

from core.io import get_meta_stream
from core.lsl_outlet import create_outlet


# server states (enum)
class E4ServerState:
    NEW__ = 'new'
    WAITING__ = 'waiting'
    NO_DEVICES__ = 'no_devices'
    DEVICES_FOUND__ = 'devices_found'
    CONNECTED_TO_DEVICE__ = "connected"
    READY_TO_SUBSCRIBE__ = "ready_to_subscribe"
    SUBSCRIBE_COMPLETED__ = "subscribe completed"
    STREAMING__ = 'streaming'


# server commands (enum)
class E4ServerCommand:
    DEVICE_LIST__ = 'device_list'
    DEVICE_CONNECT__ = 'device_connect'
    DEVICE_SUBSCRIBE__ = 'device_subscribe'
    PAUSE__ = "pause"


def msg(s_: str) -> bytes:
    return codecs.encode(s_ + '\r\n')


class Connector:

    def __init__(self) -> None:
        super().__init__()
        self.sub_codes = ['acc', 'bvp', 'gsr', 'ibi', 'tmp', 'bat', 'tag']
        self.res_codes = ['E4_Acc', 'E4_Bvp', 'E4_Gsr', 'E4_Ibi', 'E4_Temp', 'E4_Bat', 'E4_Tag']
        self.buffer_size = 4096
        self.sub_streams = 0
        self.device_id = ...
        self.outlets: dict = {}
        self.srv_state = E4ServerState.NEW__
        self.meta_stream = get_meta_stream(f"{os.path.dirname(__file__)}/spec.xml", 'xml')

    def set_devices_connected(self, num: int, devices: List[str]):
        print('%d device(s) found: %s' % (num, ', '.join([id_ for id_, name_ in devices])))
        self.srv_state = E4ServerState.NO_DEVICES__ if num == 0 else E4ServerState.DEVICES_FOUND__
        if num > 1:
            # ask user to select device
            id_ = input('Select device id: ')
            if id_ in [y for x, y in devices]:
                self.device_id = id_
            else:
                print('Invalid device id')
                exit(1)
        elif num == 1:
            id_ = devices[0][0]
            print('Selecting %s' % id_)
            self.device_id = id_

    def process_incoming_msgs(self, s: socket):
        in_msg: str = codecs.decode(s.recv(self.buffer_size))
        # parse message(s)
        in_msg_commands = [x.strip() for x in in_msg.split('\r\n')]
        for cmd in in_msg_commands:
            if len(cmd) == 0 or cmd.find(' ') == -1:
                continue
            # Handle responses to request
            if cmd[0] == 'R':
                cmd = cmd[2:]
                i = cmd.find(' ')
                # DEVICE_LIST response
                if cmd[:i] == E4ServerCommand.DEVICE_LIST__:
                    cmd = cmd[i + 1:]
                    # list devices connected
                    i = cmd.find(' ')
                    num = int(cmd[:i]) if i != -1 else 0
                    devices = []
                    if num > 0:
                        commands = cmd[i + 3:].split(' | ')
                        if len(commands) != num:
                            print('device count mismatch')
                            exit(1)
                        devices = [x.split(' ') for x in commands]
                    self.set_devices_connected(num, devices)
                # DEVICE_CONNECT response
                elif cmd[:i] == E4ServerCommand.DEVICE_CONNECT__:
                    cmd = cmd[i + 1:]
                    i = cmd.find(' ')
                    status = cmd[:i] if i != -1 else cmd
                    if status == "ERR":
                        cmd = cmd[i + 1:]
                        print('Error connecting to device: %s' % cmd)
                        exit(1)
                    elif status == "OK":
                        print('Connected to device')
                        self.srv_state = E4ServerState.CONNECTED_TO_DEVICE__
                # PAUSE response
                elif cmd[:i] == E4ServerCommand.PAUSE__:
                    cmd = cmd[i + 1:]
                    i = cmd.find(' ')
                    status = cmd[:i] if i != -1 else cmd
                    if status == "ERR":
                        cmd = cmd[i + 1:]
                        print('Error pausing streaming: %s' % cmd)
                        exit(1)
                    elif status == "ON":
                        print('Streaming on hold')
                        self.srv_state = E4ServerState.READY_TO_SUBSCRIBE__
                    elif status == "OFF":
                        print('Streaming started')
                        self.srv_state = E4ServerState.STREAMING__
                # DEVICE SUBSCRIBE response
                elif cmd[:i] == E4ServerCommand.DEVICE_SUBSCRIBE__:
                    cmd = cmd[i + 1:]
                    i = cmd.find(' ')
                    stream_type = cmd[:i]
                    cmd = cmd[i + 1:]
                    i = cmd.find(' ')
                    status = cmd[:i] if i != -1 else cmd
                    if status == "ERR":
                        cmd = cmd[i + 1:]
                        print('Error subscribing to stream %s: %s' % (stream_type, cmd))
                        exit(1)
                    elif status == "OK":
                        print('Subscribed: %s' % stream_type)
                        self.sub_streams += 1
                        if self.sub_streams == len(self.sub_codes):
                            self.srv_state = E4ServerState.SUBSCRIBE_COMPLETED__
                        else:
                            self.srv_state = E4ServerState.READY_TO_SUBSCRIBE__
            # Handle data stream
            elif self.srv_state == E4ServerState.STREAMING__:
                self.process_data_stream(cmd)

    def get_outlet(self, res_code: str) -> StreamOutlet:
        if res_code not in self.outlets:
            outlet = create_outlet(self.device_id, self.meta_stream, self.res_codes.index(res_code))
            self.outlets[res_code] = outlet
        return self.outlets[res_code]

    def process_data_stream(self, cmd: str):
        res_code: str = next(filter(cmd.startswith, self.res_codes), None)
        if res_code is not None:
            # server sent data. handle accordingly
            try:
                OUTLET = self.get_outlet(res_code)
                # only parse command if outlet has consumers
                if OUTLET.have_consumers():
                    data = list(map(float, cmd.split(' ')[1:]))
                    # three-channel output
                    if res_code == 'E4_Acc':
                        [t, x, y, z] = data
                        OUTLET.push_sample([x, y, z], t)
                    # tag output
                    elif res_code == 'E4_Tag':
                        [t] = data
                        OUTLET.push_sample([1], t)
                    # for all other outputs
                    else:
                        [t, v] = data
                        OUTLET.push_sample([v], t)
            except Exception as e:
                print('Error: ', e)
        else:
            # some other message
            print('Unknown message: ', cmd)

    def handle_outgoing_msgs(self, s: socket):
        if self.srv_state == E4ServerState.NEW__:
            # request devices list
            print('Getting list of devices...')
            s.send(msg(E4ServerCommand.DEVICE_LIST__))
            self.srv_state = E4ServerState.WAITING__
        elif self.srv_state == E4ServerState.NO_DEVICES__:
            print('No devices found!')
            exit(1)
        elif self.srv_state == E4ServerState.DEVICES_FOUND__:
            # connect to device
            print('Connecting to device...')
            s.send(msg("%s %s" % (E4ServerCommand.DEVICE_CONNECT__, self.device_id)))
            self.srv_state = E4ServerState.WAITING__
        elif self.srv_state == E4ServerState.CONNECTED_TO_DEVICE__:
            # pause streaming initially
            print('Initializing...')
            s.send(msg("%s ON" % E4ServerCommand.PAUSE__))
            self.srv_state = E4ServerState.WAITING__
        elif self.srv_state == E4ServerState.READY_TO_SUBSCRIBE__:
            # subscribe to streams
            stream = self.sub_codes[self.sub_streams]
            print('Subscribing to stream: %s' % stream)
            s.send(msg("%s %s ON" % (E4ServerCommand.DEVICE_SUBSCRIBE__, stream)))
            self.srv_state = E4ServerState.WAITING__
        elif self.srv_state == E4ServerState.SUBSCRIBE_COMPLETED__:
            # begin streaming data
            print('Requesting data')
            s.send(msg("%s OFF" % E4ServerCommand.PAUSE__))
            self.srv_state = E4ServerState.STREAMING__

    def start(self):
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((socket.gethostname(), 28000))
        while True:
            self.handle_outgoing_msgs(sock)
            self.process_incoming_msgs(sock)


if __name__ == '__main__':
    connector = Connector()
    connector.start()
