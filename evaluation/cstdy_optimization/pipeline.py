import argparse
import os.path

from fixation_detection import IVT
from reporting import FileWriter
from synthesis import PinkNoiseSimulator

import streaminghub_datamux as datamux

if __name__ == "__main__":
    # get path and dataset from CLI
    default_dir = os.path.dirname(__file__) + "/generated"
    parser = argparse.ArgumentParser()
    parser.add_argument("--basepath", type=str, default=default_dir)
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--vt", type=int, required=True)
    args = parser.parse_args()
    basepath, timeout, dataset, vt = args.basepath, args.timeout, args.dataset, args.vt

    api = datamux.API()
    streams = api.list_collection_streams(dataset)

    preprocessor = datamux.ExpressionMap(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(ld + rd) / 2",
        }
    )

    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60
    # scale noise from [-std,+std] -> [-std*scale, +std*scale]
    xy_scale = 1.0
    d_scale = 0.01

    # pass all streams with a range of vt and log generated data to file
    for stream in streams:
        attrs = stream.attrs
        subject, noise, task = attrs["subject"], attrs["noise"], attrs["task"]
        path = f"{basepath}/{subject}_{noise}_{task}"
        datamux.logging.info(f"stream_id={attrs['id']}, stream_attrs={attrs}, vt={vt}")
        # original data -> fixation/saccade -> simulated pink noise
        pipeline_C = datamux.Pipeline(
            api.attach(stream, transform=preprocessor, rate_limit=False),
            IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
            PinkNoiseSimulator(freq=freq, xy_scale=xy_scale, d_scale=d_scale, transform=None),
            FileWriter(name=f"pink_{vt}", log_dir=path, **attrs),
        )
        pipeline_C.run(timeout)

    # the generated data is truncated at start/end. compute MSE within the common chunk.
