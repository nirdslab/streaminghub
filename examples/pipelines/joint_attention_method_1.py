import streaminghub_datamux as dm

if __name__ == "__main__":

    # constants
    dataset = "ADHD_SIN"
    timeout = 10
    screen_wh = (1920, 1080)
    diag_dist = (21, 22)
    freq = 60

    # fake imports
    JointAttention: dm.PipeTask | None = None
    LogWriter: dm.SinkTask | None = None
    assert JointAttention is not None
    assert LogWriter is not None

    # hyperparameters
    threshold = 10

    # setup datamux api
    api = dm.API()

    streams = api.list_collection_streams(dataset)  # for recorded data (ADHD_SIN)
    # streams = api.list_live_streams("pupil_core")  # for live data (pupil_core)

    # get the first stream
    joint_stream = streams[0]

    # define a transform to map data into (t,x,y,d) format and handle missing values
    pre = dm.ExpressionMap(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(ld + rd) / 2",
        }
    )

    # define pipeline
    pipeline_A = dm.Pipeline(
        dm.MergedSource(
            # filter subject A data
            dm.Pipeline(
                api.attach(joint_stream, transform=pre),
                dm.Filter("subject == 'A'"),
            ).with_name("sA"),
            # filter subject B data
            dm.Pipeline(
                api.attach(joint_stream, transform=pre),
                dm.Filter("subject == 'B'"),
            ).with_name("sB"),
            # get pairwise distance between A and B
            agg="obj",
            transform=dm.ExpressionMap(
                {
                    "t": "(sA.t + sB.t) / 2",
                    "x": "abs(sA.x - sB.x)",
                    "y": "abs(sA.y - sB.y)",
                    "d": "abs(sA.d - sB.d)",
                }
            ),
        ).with_name("pairwise_distance"),
        # compute joint attention from pairwise distances
        JointAttention(threshold=threshold, transform=None).with_name("ja"),
        # write output to file
        LogWriter(name="ja_out"),
    ).with_name("joint_attention_pipeline")

    # run pipeline
    pipeline_A.run(timeout)
