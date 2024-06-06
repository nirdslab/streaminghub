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
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    path, dataset, timeout = args.path, args.dataset, args.timeout

    api = datamux.API()
    streams = api.list_collection_streams(dataset)

    for stream in streams:

        # original data
        pipeline_A = datamux.Pipeline(
            api.attach(stream, transform=None),
            LogStream(**stream.attrs, simulation="original"),
        )
        pipeline_A.run(timeout)

        # original data -> fixation/saccade -> simulated white noise
        pipeline_B = datamux.Pipeline(
            api.attach(stream, transform=None),
            IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100, transform=None),
            WhiteNoiseSimulator(freq=60, xy_scale=0.1, d_scale=0.001, transform=None),
            LogStream(**stream.attrs, simulation="white_noise", log_dir=path),
        )
        pipeline_B.run(timeout)

        # original data -> fixation/saccade -> simulated pink noise
        pipeline_C = datamux.Pipeline(
            api.attach(stream, transform=None),
            IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100, transform=None),
            PinkNoiseSimulator(freq=60, xy_scale=0.1, d_scale=0.001, transform=None),
            LogStream(**stream.attrs, simulation="pink_noise", log_dir=path),
        )
        pipeline_C.run(timeout)
