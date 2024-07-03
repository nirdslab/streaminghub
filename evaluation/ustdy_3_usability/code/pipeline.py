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
    stream_1 = streams[-2]
    stream_2 = streams[-1]
    datamux.logging.info(stream_1.attrs)
    datamux.logging.info(stream_2.attrs)

    # define a transform to map data into (t,x,y,d) format and handle missing values
    preprocessor = datamux.ExpressionMap({
        "t": "float(t)",
        "x": "float(lx + rx) / 2",
        "y": "float(ly + ry) / 2",
        "d": "float(ld + rd) / 2",
    })

    postprocessor = datamux.ExpressionMap({
        "t": "(s1.get('t', float('NaN')) + s2.get('t', float('NaN'))) / 2",
        "x": "(s1.get('x', float('NaN')) + s2.get('x', float('NaN'))) / 2",
        "y": "(s1.get('y', float('NaN')) + s2.get('y', float('NaN'))) / 2",
        "d": "(s1.get('d', float('NaN')) + s2.get('d', float('NaN'))) / 2",
    })

    # define pipeline
    pipeline_A = datamux.Pipeline(
        datamux.MergedSource(
            api.attach(stream_1, transform=preprocessor).with_name("s1"),
            api.attach(stream_2, transform=preprocessor).with_name("s2"),
            dtype="dict",
            transform=postprocessor,
        ),
        IVT(screen_wh=screen_wh, diag_dist=diag_dist, freq=freq, vt=vt, transform=None),
        LogWriter(name="ivt", **stream_1.attrs),
    )

    # run pipeline
    pipeline_A.run(timeout)
