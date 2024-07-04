import streaminghub_datamux as dm

if __name__ == "__main__":

    # constants
    dataset = "ADHD_SIN"
    timeout = 10
    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60

    # fake imports
    IVT: dm.PipeTask | None = None
    LogWriter: dm.SinkTask | None = None

    # fake assertions
    assert IVT is not None
    assert LogWriter is not None

    # hyperparameters
    vt = 10

    # setup datamux api
    api = dm.API()

    streams = api.list_collection_streams(dataset)  # for recorded data (ADHD_SIN)
    # streams = api.list_live_streams("pupil_core")  # for live data (pupil_core)

    # get the first stream
    gaze_l = streams[0]
    gaze_r = streams[1]

    # define a transform to map data into (t,x,y,d) format and handle missing values
    pre = dm.ExpressionMap(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(ld + rd) / 2",
        }
    )

    post = dm.ExpressionMap(
        {
            "t": "(sA.t + sB.t) / 2",
            "x": "(sA.x + sB.x) / 2",
            "y": "(sA.y + sB.y) / 2",
            "d": "(sA.d + sB.d) / 2",
        }
    )

    # define pipeline
    pipeline_A = dm.Pipeline(
        dm.MergedSource(
            api.attach(gaze_l, transform=pre).with_name("gaze_l"),
            api.attach(gaze_r, transform=pre).with_name("gaze_r"),
            agg="obj",
            transform=post,
        ).with_name("gaze"),
        dm.Pipeline(
            IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None).with_name("ivt"),
            LogWriter(name="log"),
        ).with_name("proc"),
    ).with_name("full")

    # run pipeline
    pipeline_A.run(timeout)
