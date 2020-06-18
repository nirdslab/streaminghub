#!/usr/bin/env python
import asyncio
import io
import os
from typing import Any, Dict

import msgpack
import zmq
import zmq.asyncio
from PIL import Image
from pylsl import StreamOutlet

from core.io import get_meta_stream
from core.lsl_outlet import create_outlet
from core.types import MetaStream

ZMQ_REQ = zmq.REQ
ZMQ_SUB = zmq.SUB
ZMQ_SUBSCRIBE = zmq.SUBSCRIBE
CONF_THRESHOLD = 0.8


class Connector(object):

    def __init__(self, device_id: str, host: str, port: int, meta: MetaStream) -> None:
        super().__init__()
        self.device_id = device_id
        self.host = host
        self.port = port
        self.meta = meta
        self.ctx = zmq.asyncio.Context()
        self.req = self.ctx.socket(ZMQ_REQ)
        self.sub = self.ctx.socket(ZMQ_SUB)
        self.topics = [
            'frame',  # camera stream (eye, world)
            'gaze',  # where you're looking at
            # 'pupil', # information about pupil (such as diameter, dilation)
            'fixations',  # starts sending data when it detects fixations (continuously sends until next fixation)
            # 'notify',  # notifications
            # 'logging'  # for logging
        ]
        self.stream_idx = {
            'frame': 0,
            'gaze.0': 1,
            'gaze.1': 2,
            'fixations': 3
        }
        self.outlets: Dict[str, StreamOutlet] = {}
        self.sub_port: int = ...

    async def get_sub_port(self) -> int:
        self.req.connect(f"tcp://{self.host}:{self.port}")
        print('Opened REQ socket.')
        self.req.send_string('SUB_PORT')
        sub_port = int(await self.req.recv_string())
        print(f'Received SUB_PORT. {self.sub_port}')
        return sub_port

    def get_outlet(self, stream_id: str) -> StreamOutlet:
        if stream_id not in self.outlets:
            idx = self.stream_idx[stream_id]
            stream = self.meta.streams[idx]
            self.outlets[stream_id] = create_outlet(self.device_id, self.meta.device, stream)
        return self.outlets[stream_id]

    def subscribe(self):
        self.sub.connect(f'tcp://{self.host}:{self.sub_port}')
        print('Opened SUB socket')
        for sub_id in self.topics:
            self.sub.setsockopt_string(ZMQ_SUBSCRIBE, sub_id)
            print(f'Subscribed to: {sub_id}')
        print('Subscription Completed.')

    def emit(self, topic: str, message: dict, extra) -> Any:
        ts = message[b'timestamp']
        if topic.startswith('gaze'):
            # decode message
            [gaze_pos_x, gaze_pos_y] = message[b'norm_pos']
            gaze_conf = message[b'confidence']
            # push to LSL stream if data point has acceptable confidence
            if gaze_conf > CONF_THRESHOLD:
                self.get_outlet(f'gaze.{topic[5]}').push_sample([gaze_pos_x, gaze_pos_y, gaze_conf], ts)
        elif topic.startswith('fixations'):
            # decode message
            [fxn_pos_x, fxn_pos_y] = message[b'norm_pos']
            fxn_dispersion = message[b'dispersion']
            fxn_d = message[b'duration']
            fxn_conf = message[b'confidence']
            # push to LSL stream if data point has acceptable confidence
            if fxn_conf > CONF_THRESHOLD:
                self.get_outlet('fixations').push_sample([fxn_pos_x, fxn_pos_y, fxn_dispersion, fxn_d, fxn_conf], ts)
        elif topic.startswith('frame'):
            # push image data to LSL stream
            [r, g, b] = extra
            # TODO check
            self.get_outlet('frame').push_chunk([r, g, b], ts)

    async def run(self):
        self.sub_port = await self.get_sub_port()
        self.subscribe()
        while True:
            try:
                # receive raw data (bytes)
                data: list = await self.sub.recv_multipart()
                # content of data after being parsed
                topic: str = data[0].decode()
                message: dict = msgpack.loads(data[1])
                extra: list = data[2:]
                # special case
                if str.startswith(topic, 'frame'):
                    image: Image.Image = Image.open(io.BytesIO(extra[0]))
                    [r, g, b] = [image.getdata(0), image.getdata(1), image.getdata(2)]
                    self.emit(topic, message, [r, g, b])
                    continue
                # general case
                self.emit(topic, message, None)
            except InterruptedError:
                break


async def main():
    # get meta-stream for pupil core
    meta = get_meta_stream(f"{os.path.dirname(__file__)}/spec.json", "json")
    # set random device id
    device_id = "1234564321"
    connector = Connector(device_id, '127.0.0.1', 50020, meta)
    await connector.run()


if __name__ == '__main__':
    asyncio.run(main())
