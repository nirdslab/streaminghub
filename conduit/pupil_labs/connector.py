#!/usr/bin/env python
import asyncio
import io
from typing import Any, Dict

import msgpack
import zmq
import zmq.asyncio
from PIL import Image
from pylsl import StreamOutlet

from core.lsl_outlet import create_outlet
from pupil_labs.descriptor import streams, device_info

ZMQ_REQ = zmq.REQ
ZMQ_SUB = zmq.SUB
ZMQ_SUBSCRIBE = zmq.SUBSCRIBE
CONF_THRESHOLD = 0.8

OUTLETS: Dict[str, StreamOutlet] = {}
DEVICE_ID = '1'


def get_outlet(d: str) -> StreamOutlet:
    if d not in OUTLETS:
        OUTLETS[d] = create_outlet(DEVICE_ID, device_info, streams[d])
    return OUTLETS[d]


class Parser(object):

    def __init__(self, topic) -> None:
        super().__init__()
        self.topic: str = topic

    def parse(self, message, extra) -> Any:
        t = self.topic
        if self.topic.startswith('gaze'):
            # decode message
            [gaze_pos_x, gaze_pos_y] = message[b'norm_pos']
            gaze_conf = message[b'confidence']
            gaze_ts = message[b'timestamp']
            # push to LSL stream if data point has acceptable confidence
            if gaze_conf > CONF_THRESHOLD:
                eye_id = int(self.topic.strip('.')[-1])
                stream_id = f'gaze.{eye_id}'
                OUTLET = get_outlet(stream_id)
                OUTLET.push_sample([gaze_pos_x, gaze_pos_y, gaze_conf], gaze_ts)
        elif self.topic.startswith('fixations'):
            # decode message
            [fxn_pos_x, fxn_pos_y] = message[b'norm_pos']
            fxn_dispersion = message[b'dispersion']
            fxn_d = message[b'duration']
            fxn_conf = message[b'confidence']
            fxn_ts = message[b'timestamp']
            # push to LSL stream if data point has acceptable confidence
            if fxn_conf > CONF_THRESHOLD:
                stream_id = 'fixations'
                OUTLET = get_outlet(stream_id)
                OUTLET.push_sample([fxn_pos_x, fxn_pos_y, fxn_dispersion, fxn_d, fxn_conf], fxn_ts)
        elif self.topic.startswith('frame') and len(extra) > 0:
            # decode message
            frame_ts = message[b'timestamp']
            # push frame to LSL stream
            stream_id = 'camera'
            OUTLET = get_outlet(stream_id)
            OUTLET.push_sample(extra, frame_ts)  # FIXME


async def main():
    # remote host / port
    _host: str = '127.0.0.1'
    _port: int = 50020
    _sub_port: int = ...
    _ctx = zmq.asyncio.Context()

    # GET SUB_PORT
    print('# GET SUB_PORT #')
    # open REQ socket
    print('Opening REQ socket...', end=' ', flush=True)
    _req = _ctx.socket(ZMQ_REQ)
    _req.connect(f"tcp://{_host}:{_port}")
    print('OK')
    # receive SUB port
    print('Querying SUB_PORT...', end=' ', flush=True)
    _req.send_string('SUB_PORT')
    _sub_port = int(await _req.recv_string())
    print(f'{_sub_port}')
    # close REQ socket
    print('Closing REQ socket...', end=' ', flush=True)
    _req.close()
    print('DONE')

    # SET UP SUBSCRIPTIONS
    print('# SET UP SUBSCRIPTIONS #')
    print('Opening SUB socket...', end=' ', flush=True)
    _sub = _ctx.socket(ZMQ_SUB)
    _sub.connect(f'tcp://{_host}:{_sub_port}')
    print('OK')

    # subscribe to streams
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'gaze')  # where you're looking at
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'pupil')  # information about pupil (such as diameter, dilation)
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'fixations')  # starts sending data when it detects fixations (continuously sends until next fixation)
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'frame')  # camera stream (eye, world)
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'notify') # notifications
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'logging') # for logging

    _parsers = {}

    while True:
        try:
            # receive raw data (bytes)
            data = await _sub.recv_multipart()
            # content of data after being parsed
            [topic, payload, *_extra] = data
            topic = topic.decode()
            message = msgpack.loads(payload)

            # handle special payloads
            if len(_extra) > 0:
                # decode bytes
                if str.startswith(topic, 'frame'):
                    # interpret as images
                    _extra = list(map(Image.open, map(io.BytesIO, _extra)))
                else:
                    print('Unsupported byte data received, ignoring.')
            # parse data
            Parser(topic).parse(message, _extra)
        except InterruptedError:
            break


if __name__ == '__main__':
    asyncio.run(main())
