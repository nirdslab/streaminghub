import os.path

import streaminghub_datamux as datamux
from gaze.fixation_detection import IVT
from gaze.reporting import LogStream
from gaze.synthesis import PinkNoiseSimulator, WhiteNoiseSimulator

if __name__ == "__main__":
    datamux.init()
    output_dir = os.path.dirname(__file__) + "/generated"

    api = datamux.API()
    collections = api.list_collections()
    collection_names = [c.name for c in collections]
    print(collection_names)
    adhd_sin_streams = api.list_collection_streams("ADHD_SIN")
    n_back_streams = []
    # n_back_streams = api.list_collection_streams("n_back")

    for stream in [*adhd_sin_streams, *n_back_streams]:

        # original data
        pipeline_A = datamux.Pipeline(
            api.attach(stream, transform=None),
            LogStream(**stream.attrs, simulation="original"),
        )
        pipeline_A.run()

        # original data -> fixation/saccade -> simulated white noise
        pipeline_B = datamux.Pipeline(
            api.attach(stream, transform=None),
            IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100, transform=None),
            WhiteNoiseSimulator(freq=60, xy_scale=0.1, d_scale=0.001, transform=None),
            LogStream(**stream.attrs, simulation="white_noise", log_dir=output_dir),
        )
        pipeline_B.run()

        # original data -> fixation/saccade -> simulated pink noise
        pipeline_C = datamux.Pipeline(
            api.attach(stream, transform=None),
            IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100, transform=None),
            PinkNoiseSimulator(freq=60, xy_scale=0.1, d_scale=0.001, transform=None),
            LogStream(**stream.attrs, simulation="pink_noise", log_dir=output_dir),
        )
        pipeline_C.run()
