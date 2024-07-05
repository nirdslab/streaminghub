import streaminghub_datamux as dm


class LogWriter(dm.SinkTask):

    def __init__(self) -> None:
        super().__init__()

    def step(self, input) -> int | None:
        self.logger.info(input)


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
    api = dm.API()

    streams = api.list_collection_streams(dataset)  # for recorded data (ADHD_SIN)
    # streams = api.list_live_streams("pupil_core")  # for live data (pupil_core)

    # get the first stream
    eye_stream = streams[0]

    # define a transform to map data into (t,x,y,d) format and handle missing values
    merge = dm.ExpressionMap(
        {
            "t": "t",
            "x": "(lx + rx) / 2",
            "y": "(ly + ry) / 2",
            "d": "(ld + rd) / 2",
        }
    )

    cast = dm.ExpressionMap(
        {
            "t": "float(t)",
            "x": "float(x)",
            "y": "float(y)",
            "d": "float(d)",
        }
    )

    # define pipeline
    pipeline_A = dm.Pipeline(
        api.attach(eye_stream, transform=merge).with_name("eye"),
        dm.Filter("not (isnan(x) or isnan(y) or isnan(d))"),
        dm.Transform(cast),
        LogWriter().with_name("log"),
    ).with_name("simple_logger")

    # run pipeline
    pipeline_A.run(timeout)
