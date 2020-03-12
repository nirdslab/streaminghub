#!/usr/bin/env python
import io
from pprint import pprint

import msgpack
import zmq
from PIL import Image

ZMQ_REQ = zmq.REQ
ZMQ_SUB = zmq.SUB
ZMQ_SUBSCRIBE = zmq.SUBSCRIBE


def recv_sub_port(_host: str, _port: int, _sock: zmq.Socket) -> int:
    """
    Communicate with PupilLabs Network API, and get SUB_PORT

    :param _host: hostname
    :param _port: port
    :param _sock: zeromq socket
    :return: SUB_PORT - port on which to subscribe on
    """
    # query SUB_PORT
    _sock.send_string('SUB_PORT')
    _recv = _sock.recv_string()
    return int(_recv)


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
    _sub_port = recv_sub_port(_host, _port, _req)
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
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'pupil')  # pupil diameter, dilation, etc/
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'fixations')  # starts sending data when it detects fixations (continuously sends until next fixation)
    _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'frame')  # camera stream (eye, world)
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'notify') # notifications
    # _sub.setsockopt_string(ZMQ_SUBSCRIBE, 'logging') # for logging

    while True:
        try:
            # receive raw data (bytes)
            data = _sub.recv_multipart()
            # content of data after being parsed
            [topic, payload, *_bytes] = data
            topic = topic.decode()
            message = msgpack.loads(payload)
            if len(_bytes) > 0:
                # decode bytes
                if str.startswith(topic, 'frame'):
                    # decode _bytes as image
                    image: Image.Image = Image.open(io.BytesIO(_bytes[0]))
                    # TODO do something with the images. don't forget to use the topic to find what the image is (eye 1 / eye 2 / world)
                else:
                    print('Unsupported byte data received, ignoring.')
            print(f"{topic}: {message}")
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

            # f = open("fixations.txt", "a")
            # f.write("\n{}".format(str(msg)))
            # f.close()

            # break
            # print(topic)
            # print(msg)
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
        except KeyboardInterrupt:
            break
        except BaseException as e:
            pprint(e)


if __name__ == '__main__':
    main()
