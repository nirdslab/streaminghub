#!/usr/bin/env python
import asyncio
import io
import os
from typing import Any, Dict

import msgpack
import numpy as np
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
            'frame.world',  # camera stream (eye, world)
            'gaze.3d.0.',  # where you're looking at
            'gaze.3d.1.',  # where you're looking at
            # 'pupil', # information about pupil (such as diameter, dilation)
            'fixations',  # starts sending data when it detects fixations (continuously sends until next fixation)
            # 'notify',  # notifications
            # 'logging'  # for logging
        ]
        self.stream_idx = {
            'frame.world': 0,
            'gaze.3d.0.': 1,
            'gaze.3d.1.': 2,
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

    def emit(self, topic: str, message: dict, image: np.array) -> Any:
        ts = message['timestamp']
        if topic.startswith('gaze.3d.'):
            # decode message
            [gaze_pos_x, gaze_pos_y] = message['norm_pos']
            gaze_conf = message['confidence']
            # push to LSL stream if data point has acceptable confidence
            if gaze_conf > CONF_THRESHOLD:
                self.get_outlet(topic[:10]).push_sample([gaze_pos_x, gaze_pos_y, gaze_conf], ts)
        elif topic.startswith('fixations'):
            # decode message
            [fxn_pos_x, fxn_pos_y] = message['norm_pos']
            fxn_dispersion = message['dispersion']
            fxn_d = message['duration']
            fxn_conf = message['confidence']
            # push to LSL stream if data point has acceptable confidence
            if fxn_conf > CONF_THRESHOLD:
                self.get_outlet(topic[:9]).push_sample([fxn_pos_x, fxn_pos_y, fxn_dispersion, fxn_d, fxn_conf], ts)
        elif image is not None:
            # push image data to LSL stream
            [r, g, b] = image
            # TODO only sending (0,0) pixel for now, fix to send all pixels
            self.get_outlet(topic[:11]).push_sample([r[0][0], g[0][0], b[0][0]], ts)

    async def run(self):
        self.sub_port = await self.get_sub_port()
        self.subscribe()
        print('Started Data Stream. Use SIGINT to terminate.')
        while True:
            try:
                # receive raw data (bytes)
                [topic, payload, *extra] = await self.sub.recv_multipart()
                topic = topic.decode()
                image = None
                # world camera
                if topic.startswith('frame.world'):
                    image = np.transpose(np.asarray(Image.open(io.BytesIO(extra[0])).convert('RGB')))
                # payload
                payload = msgpack.loads(payload)
                self.emit(topic, payload, image)
            except KeyboardInterrupt:
                print('Received Interrupt. Stopping...')
                break
        print('Stopped.')


async def main():
    # get meta-stream for pupil model
    meta = get_meta_stream(f"{os.path.dirname(__file__)}/spec.json", "json")
    # set random device id
    device_id = "1234564321"
    connector = Connector(device_id, '127.0.0.1', 50020, meta)
    await connector.run()


if __name__ == '__main__':
    asyncio.run(main())
