from fixation_detection import IVT
from reporting import LogStream

import streaminghub_datamux as datamux

if __name__ == "__main__":

    # constants
    dataset = "ADHD_SIN"
    timeout = 30
    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60

    # hyperparameters
    vt = 10

    # setup datamux api
    datamux.init()
    api = datamux.API()

    # stream = api.list_live_streams("pupil_core")[0]  # for live data (pupil_core)
    stream = api.list_collection_streams(dataset)[0]  # for recorded data (ADHD_SIN)

    # define a transform to map source data to the pipeline
    preprocessor = datamux.ExpressionMap(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(lx + ly + rx + ry) / 4",
        }
    )

    # define pipeline
    pipeline_A = datamux.Pipeline(
        api.attach(stream, transform=preprocessor),
        IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
        LogStream(**stream.attrs, simulation="original"),
    )

    # run pipeline
    pipeline_A.run(timeout)