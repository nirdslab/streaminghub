#!/usr/bin/env python3
import codecs
import socket
from typing import List, Dict

from pylsl import StreamOutlet

from core.lsl_outlet import create_outlet


# server states
class SRV_STATES:
    NEW__ = 'new'
    WAITING__ = 'waiting'
    NO_DEVICES__ = 'no_devices'
    DEVICES_FOUND__ = 'devices_found'
    CONNECTED_TO_DEVICE__ = "connected"
    READY_TO_SUBSCRIBE__ = "ready_to_subscribe"
    SUBSCRIBE_COMPLETED__ = "subscribe completed"
    STREAMING__ = 'streaming'


# server commands
class SRV_COMMANDS:
    DEVICE_LIST__ = 'device_list'
    DEVICE_CONNECT__ = 'device_connect'
    DEVICE_SUBSCRIBE__ = 'device_subscribe'
    PAUSE__ = "pause"


# server subscriptions
SRV_SUBSCRIPTIONS = ['acc', 'bvp', 'gsr', 'ibi', 'tmp', 'bat', 'tag']
SRV_BUF_SIZE = 4096

# server stream id mapping
SRV_STREAM_ID_MAP = {
    'E4_Acc': 'acc',
    'E4_Bvp': 'bvp',
    'E4_Gsr': 'gsr',
    'E4_Ibi': 'ibi',
    'E4_Hr': 'hr',
    'E4_Temperature': 'tmp',
    'E4_Battery': 'bat',
    'E4_Tag': 'tag'
}

OUTLETS: Dict[str, StreamOutlet] = {}

# State
STATE = SRV_STATES.NEW__
DEVICE_ID: str = ''
stream_i = 0


def msg(s_: str) -> bytes:
    return codecs.encode(s_ + '\r\n')


def set_devices_connected(num: int, devices: List[str]):
    global DEVICE_ID
    print('%d device(s) found: %s' % (num, ', '.join([id_ for id_, name_ in devices])))
    set_state(SRV_STATES.NO_DEVICES__ if num == 0 else SRV_STATES.DEVICES_FOUND__)
    if num > 1:
        # ask user to select device
        id_ = input('Select device id: ')
        if id_ in [y for x, y in devices]:
            DEVICE_ID = id_
        else:
            print('Invalid device id')
            exit(1)
    elif num == 1:
        id_ = devices[0][0]
        print('Selecting %s' % id_)
        DEVICE_ID = id_


def set_state(state: str):
    global STATE
    STATE = state


def process_incoming_msgs():
    global stream_i
    in_msg: str = codecs.decode(s.recv(SRV_BUF_SIZE))
    # parse message(s)
    in_msg_cmds = [x.strip() for x in in_msg.split('\r\n')]
    for cmd in in_msg_cmds:
        if len(cmd) == 0 or cmd.find(' ') == -1:
            continue
        # Handle responses to request
        if cmd[0] == 'R':
            cmd = cmd[2:]
            i = cmd.find(' ')
            # DEVICE_LIST response
            if cmd[:i] == SRV_COMMANDS.DEVICE_LIST__:
                cmd = cmd[i + 1:]
                # list devices connected
                i = cmd.find(' ')
                num = int(cmd[:i]) if i != -1 else 0
                devices = []
                if num > 0:
                    cmds = cmd[i + 3:].split(' | ')
                    if len(cmds) != num:
                        print('device count mismatch')
                        exit(1)
                    devices = [x.split(' ') for x in cmds]
                set_devices_connected(num, devices)
            # DEVICE_CONNECT response
            elif cmd[:i] == SRV_COMMANDS.DEVICE_CONNECT__:
                cmd = cmd[i + 1:]
                i = cmd.find(' ')
                status = cmd[:i] if i != -1 else cmd
                if status == "ERR":
                    cmd = cmd[i + 1:]
                    print('Error connecting to device: %s' % cmd)
                    exit(1)
                elif status == "OK":
                    print('Connected to device')
                    set_state(SRV_STATES.CONNECTED_TO_DEVICE__)
            # PAUSE response
            elif cmd[:i] == SRV_COMMANDS.PAUSE__:
                cmd = cmd[i + 1:]
                i = cmd.find(' ')
                status = cmd[:i] if i != -1 else cmd
                if status == "ERR":
                    cmd = cmd[i + 1:]
                    print('Error pausing streaming: %s' % cmd)
                    exit(1)
                elif status == "ON":
                    print('Streaming on hold')
                    set_state(SRV_STATES.READY_TO_SUBSCRIBE__)
                elif status == "OFF":
                    print('Streaming started')
                    set_state(SRV_STATES.STREAMING__)
            # DEVICE SUBSCRIBE response
            elif cmd[:i] == SRV_COMMANDS.DEVICE_SUBSCRIBE__:
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
                    stream_i += 1
                    if stream_i == len(SRV_SUBSCRIPTIONS):
                        set_state(SRV_STATES.SUBSCRIBE_COMPLETED__)
                    else:
                        set_state(SRV_STATES.READY_TO_SUBSCRIBE__)
        # Handle data stream
        elif STATE == SRV_STATES.STREAMING__:
            process_data_stream(cmd)


def get_outlet(d: str) -> StreamOutlet:
    if d not in OUTLETS:
        OUTLETS[d] = create_outlet(DEVICE_ID, device_info, streams[SRV_STREAM_ID_MAP[d]])
    return OUTLETS[d]


def process_data_stream(cmd: str):
    d = next(filter(lambda c: cmd.startswith(c), SRV_STREAM_ID_MAP), None)
    if d is not None:
        # server sent data. handle accordingly
        try:
            OUTLET = get_outlet(d)
            # only parse command if outlet has consumers
            if OUTLET.have_consumers():
                data = list(map(float, cmd.split(' ')[1:]))
                # three-channel output
                if d == 'E4_Acc':
                    [t, x, y, z] = data
                    OUTLET.push_sample([x, y, z], t)
                # tag output
                elif d == 'E4_Tag':
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
        print('Unknown message: %s' % cmd)


def handle_outgoing_msgs():
    if STATE == SRV_STATES.NEW__:
        # request devices list
        print('Getting list of devices...')
        s.send(msg(SRV_COMMANDS.DEVICE_LIST__))
        set_state(SRV_STATES.WAITING__)
    elif STATE == SRV_STATES.NO_DEVICES__:
        print('No devices found!')
        exit(1)
    elif STATE == SRV_STATES.DEVICES_FOUND__:
        # connect to device
        print('Connecting to device...')
        s.send(msg("%s %s" % (SRV_COMMANDS.DEVICE_CONNECT__, DEVICE_ID)))
        set_state(SRV_STATES.WAITING__)
    elif STATE == SRV_STATES.CONNECTED_TO_DEVICE__:
        # pause streaming initially
        print('Initializing...')
        s.send(msg("%s ON" % SRV_COMMANDS.PAUSE__))
        set_state(SRV_STATES.WAITING__)
    elif STATE == SRV_STATES.READY_TO_SUBSCRIBE__:
        # subscribe to streams
        stream = SRV_SUBSCRIPTIONS[stream_i]
        print('Subscribing to stream: %s' % stream)
        s.send(msg("%s %s ON" % (SRV_COMMANDS.DEVICE_SUBSCRIBE__, stream)))
        set_state(SRV_STATES.WAITING__)
    elif STATE == SRV_STATES.SUBSCRIBE_COMPLETED__:
        # begin streaming data
        print('Requesting data')
        s.send(msg("%s OFF" % SRV_COMMANDS.PAUSE__))
        set_state(SRV_STATES.STREAMING__)


if __name__ == '__main__':
    # Create socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 28000))
    # event loop
    while True:
        handle_outgoing_msgs()
        process_incoming_msgs()
