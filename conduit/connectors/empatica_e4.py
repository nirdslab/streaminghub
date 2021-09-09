#!/usr/bin/env python3
import codecs
import os
import socket
from typing import List

from pylsl import StreamOutlet

from dfs import get_datasource_spec
from dfs.lsl_outlet import create_outlet


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
    self.stream_ids = ['acc', 'bvp', 'gsr', 'ibi', 'tmp', 'bat', 'tag']
    self.res_ids = ['E4_Acc', 'E4_Bvp', 'E4_Gsr', 'E4_Ibi', 'E4_Temp', 'E4_Bat', 'E4_Tag']
    self.buffer_size = 4096
    self.sub_streams = 0
    self.device_list = ...
    self.device_id = ...
    self.outlets: dict = {}
    self.server_state = E4ServerState.NEW__
    self.datasource_spec = get_datasource_spec(f"{os.path.dirname(__file__)}/../datasources/empatica_e4.json", 'json')

  def set_device_list(self, devices: List[str]):
    self.device_list = devices
    num = len(devices)
    print(f"{num} device(s) found: {devices}")
    self.server_state = E4ServerState.NO_DEVICES__ if num == 0 else E4ServerState.DEVICES_FOUND__
    if num > 1:
      while True:
        # prompt user to select device
        device_id = input(f'Select device: ')
        if self.select_device(device_id):
          break
    elif num == 1:
      self.select_device(devices[0])

  def select_device(self, device_id: str) -> bool:
    if device_id in self.device_list:
      print(f'Selected Device: {device_id}')
      self.device_id = device_id
      return True
    else:
      print(f'Invalid selection. Please select one from: {self.device_list}')
      return False

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
              print(f'device count mismatch: expected {num}, got {len(commands)} instead')
              exit(1)
            devices = [x.split(' ')[0].strip() for x in commands]
          self.set_device_list(devices)
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
            self.server_state = E4ServerState.CONNECTED_TO_DEVICE__
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
            self.server_state = E4ServerState.READY_TO_SUBSCRIBE__
          elif status == "OFF":
            print('Streaming started')
            self.server_state = E4ServerState.STREAMING__
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
            if self.sub_streams == len(self.stream_ids):
              self.server_state = E4ServerState.SUBSCRIBE_COMPLETED__
            else:
              self.server_state = E4ServerState.READY_TO_SUBSCRIBE__
      # Handle data stream
      elif self.server_state == E4ServerState.STREAMING__:
        self.process_data_stream(cmd)

  def get_outlet(self, res_code: str) -> StreamOutlet:
    if res_code not in self.outlets:
      _spec = self.datasource_spec
      _stream_id = self.stream_ids[self.res_ids.index(res_code)]
      self.outlets[res_code] = create_outlet(self.device_id, _spec.device, _spec.streams[_stream_id])
    return self.outlets[res_code]

  def process_data_stream(self, cmd: str):
    res_code: str = next(filter(cmd.startswith, self.res_ids), None)
    if res_code is not None:
      # server sent data. handle accordingly
      print(cmd)
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
            OUTLET.push_sample([0], t)
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
    if self.server_state == E4ServerState.NEW__:
      # request devices list
      print('Getting list of devices...')
      s.send(msg(E4ServerCommand.DEVICE_LIST__))
      self.server_state = E4ServerState.WAITING__
    elif self.server_state == E4ServerState.NO_DEVICES__:
      print('No devices found!')
      exit(1)
    elif self.server_state == E4ServerState.DEVICES_FOUND__:
      # connect to device
      print('Connecting to device...')
      s.send(msg("%s %s" % (E4ServerCommand.DEVICE_CONNECT__, self.device_id)))
      self.server_state = E4ServerState.WAITING__
    elif self.server_state == E4ServerState.CONNECTED_TO_DEVICE__:
      # pause streaming initially
      print('Initializing...')
      s.send(msg("%s ON" % E4ServerCommand.PAUSE__))
      self.server_state = E4ServerState.WAITING__
    elif self.server_state == E4ServerState.READY_TO_SUBSCRIBE__:
      # subscribe to streams
      stream = self.stream_ids[self.sub_streams]
      print('Subscribing to stream: %s' % stream)
      s.send(msg("%s %s ON" % (E4ServerCommand.DEVICE_SUBSCRIBE__, stream)))
      self.server_state = E4ServerState.WAITING__
    elif self.server_state == E4ServerState.SUBSCRIBE_COMPLETED__:
      # begin streaming data
      print('Requesting data')
      s.send(msg("%s OFF" % E4ServerCommand.PAUSE__))
      self.server_state = E4ServerState.STREAMING__

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
