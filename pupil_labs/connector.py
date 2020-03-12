#!/usr/bin/env python
import io
from pprint import pprint
from typing import Any

import msgpack
import zmq
from PIL import Image

ZMQ_REQ = zmq.REQ
ZMQ_SUB = zmq.SUB
ZMQ_SUBSCRIBE = zmq.SUBSCRIBE


class Parser(object):

    def __init__(self, topic) -> None:
        super().__init__()
        self.topic = topic

    def parse(self, message, extra) -> Any:
        print(f"{self.topic} - {message}")

        # TODO do something if topic = 'frame' and len(extra) > 0. use topic to find what the image is (eye 1 / eye 2 / world)
        # print("\n{}:{}".format('topic', msg.get('topic')))
        # # print("{}:{}".format('base_data', msg.get('base_data')))
        # print("{}:{}".format('timestamp', msg.get('timestamp')))
        # print("{}:{}".format('norm_pos', msg.get('norm_pos')))
        # print("{}:{}".format('confidence', msg.get('confidence')))

        # Fixations
        # print("\n{}:{}".format('topic',msg.get('topic')))
        # print("{}:{}".format('method',msg.get('method')))
        # print("{}:{}".format('norm_pos',msg.get('norm_pos')))
        # print("{}:{}".format('duration',msg.get('duration')))
        # print("{}:{}".format('confidence',msg.get('confidence')))
        # print("{}:{}".format('timestamp',msg.get('timestamp')))
        # print("{}:{}".format('dispersion',msg.get('dispersion')))

        # surfaces = loads(msg, encoding='utf-8')
        # filtered_surface = {k: v for k, v in surfaces.items() if surfaces['name'] == surface_name}
        # try:
        #     # note that we may have more than one gaze position data point (this is expected behavior)
        #     gaze_positions = filtered_surface['gaze_on_surfaces']
        #     for gaze_pos in gaze_positions:
        #         norm_gp_x, norm_gp_y = gaze_pos['norm_pos']
        #
        #         # only print normalized gaze positions within the surface bounds
        #         if (0 <= norm_gp_x <= 1 and 0 <= norm_gp_y <= 1):
        #             print("gaze on surface: {}\t, normalized coordinates: {},{}".format(surface_name, norm_gp_x, norm_gp_y))
        # except:
        #     pass


def main():
    # remote host / port
    _host: str = '127.0.0.1'
    _port: int = 50020
    _sub_port: int = ...
    _ctx = zmq.Context()

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
    _sub_port = int(_req.recv_string())
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
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'pupil')  # information about pupil (such as diameter, dilation)
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'fixations')  # starts sending data when it detects fixations (continuously sends until next fixation)
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'frame')  # camera stream (eye, world)
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'notify') # notifications
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'logging') # for logging

    _parsers = {}

    while True:
        try:
            # receive raw data (bytes)
            data = _sub.recv_multipart()
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
        except KeyboardInterrupt:
            break
        except BaseException as e:
            pprint(e)


if __name__ == '__main__':
    main()
