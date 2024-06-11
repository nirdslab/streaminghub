import argparse
import os.path

import streaminghub_datamux as datamux
from gaze.fixation_detection import IVT
from gaze.reporting import LogStream
from gaze.synthesis import PinkNoiseSimulator, WhiteNoiseSimulator

if __name__ == "__main__":

    datamux.init()

    # get path and dataset from CLI
    default_dir = os.path.dirname(__file__) + "/generated"
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default=default_dir)
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    path, dataset, timeout = args.path, args.dataset, args.timeout

    # api = datamux.RemoteAPI("websocket", "json")
    # api.connect("localhost", 8765)
    api = datamux.API()
    streams = api.list_collection_streams(dataset)

    preprocessor = datamux.ExpressionMapper(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(lx + ly + rx + ry) / 4",
        }
    )

    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60
    vt = 10
    # scale noise from [-std,+std] -> [-std*scale, +std*scale]
    xy_scale = 1.0
    d_scale = 0.001

    for stream in streams:

        # original data
        pipeline_A = datamux.Pipeline(
            api.attach(stream, transform=preprocessor),
            LogStream(**stream.attrs, simulation="original"),
        )
        pipeline_A.run(timeout)

        # original data -> fixation/saccade -> simulated white noise
        pipeline_B = datamux.Pipeline(
            api.attach(stream, transform=preprocessor),
            IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
            WhiteNoiseSimulator(freq=freq, xy_scale=xy_scale, d_scale=d_scale, transform=None),
            LogStream(**stream.attrs, simulation="white_noise", log_dir=path),
        )
        pipeline_B.run(timeout)

        # original data -> fixation/saccade -> simulated pink noise
        pipeline_C = datamux.Pipeline(
            api.attach(stream, transform=preprocessor),
            IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
            PinkNoiseSimulator(freq=freq, xy_scale=xy_scale, d_scale=d_scale, transform=None),
            LogStream(**stream.attrs, simulation="pink_noise", log_dir=path),
        )
        pipeline_C.run(timeout)
