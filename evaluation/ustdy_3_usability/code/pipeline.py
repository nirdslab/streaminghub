from fixation_detection import IVT
from reporting import LogWriter

import streaminghub_datamux as datamux

if __name__ == "__main__":

    # constants
    dataset = "ADHD_SIN"
    timeout = 10
    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60

    # hyperparameters
    vt = 10

    # setup datamux api
    api = datamux.API()

    streams = api.list_collection_streams(dataset)  # for recorded data (ADHD_SIN)
    # streams = api.list_live_streams("pupil_core")  # for live data (pupil_core)

    # get the first stream
    streamA = streams[-2]
    streamB = streams[-1]

    # define a transform to map data into (t,x,y,d) format and handle missing values
    preprocessor = datamux.ExpressionMap({
        "t": "t",
        "x": "(lx + rx) / 2",
        "y": "(ly + ry) / 2",
        "d": "(ld + rd) / 2",
    })

    postprocessor = datamux.ExpressionMap({
        "t": "(sA.t + sB.t) / 2",
        "x": "(sA.x + sB.x) / 2",
        "y": "(sA.y + sB.y) / 2",
        "d": "(sA.d + sB.d) / 2",
    })

    # define pipeline
    pipeline_A = datamux.Pipeline(
        datamux.MergedSource(
            api.attach(streamA, transform=preprocessor).with_name("sA"),
            api.attach(streamB, transform=preprocessor).with_name("sB"),
            agg="obj",
            transform=postprocessor,
        ).with_name("part1"),
        # datamux.Pipeline(
            IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None).with_name("ivt"),
            LogWriter(name="log"),
        # ).with_name("part2"),
    ).with_name("full")

    # run pipeline
    pipeline_A.run(timeout)
