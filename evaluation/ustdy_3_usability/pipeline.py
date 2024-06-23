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

    streams = api.list_collection_streams(dataset)  # for recorded data (ADHD_SIN)
    # stream = api.list_live_streams("pupil_core")  # for live data (pupil_core)

    # get the first stream
    stream = streams[0]
    datamux.logging.info(stream.attrs)

    # define a transform to map data into (t,x,y,d) format and handle missing values
    preprocessor = datamux.ExpressionMap({
        "t": "float(t)",
        "x": "float(lx + rx) / 2",
        "y": "float(ly + ry) / 2",
        "d": "float(ld + rd) / 2",
    })

    # define pipeline
    pipeline_A = datamux.Pipeline(
        api.attach(stream, transform=preprocessor),
        # IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
        LogStream(**stream.attrs, simulation="ivt"),
    )

    # run pipeline
    pipeline_A.run(timeout)
