from typing import NamedTuple

RunConfig = NamedTuple("RunConfig", [("dataset_name", str), ("num_runs", int), ("num_points", int)])

data_config: dict = dict(
    ADHD_SIN=dict(
        collection_id="ADHD_SIN",
        stream_id="gaze",
        attrs=dict(
            noise="0",
            participant="012",
            question="10",
        ),
    ),
    adhd_sin_h5=dict(
        collection_id="adhd_sin_h5",
        stream_id="gaze",
        attrs=dict(
            noise="0",
            participant="12",
            question="10",
        ),
    ),
    battleship_gaze=dict(
        collection_id="battleship_gaze",
        stream_id="gaze",
        attrs=dict(
            session="1",
            stream_name="gaze",
        ),
    ),
    tdbrain=dict(
        collection_id="tdbrain",
        stream_id="eeg",
        attrs=dict(
            subject="19681349",
            session="1",
            task="restEC",
        ),
    ),
)

runs = [
    RunConfig("ADHD_SIN", 10, 60),
    RunConfig("ADHD_SIN", 10, 120),
    RunConfig("ADHD_SIN", 10, 240),
    RunConfig("ADHD_SIN", 10, 480),
    RunConfig("adhd_sin_h5", 10, 60),
    RunConfig("adhd_sin_h5", 10, 120),
    RunConfig("adhd_sin_h5", 10, 240),
    RunConfig("adhd_sin_h5", 10, 480),
    RunConfig("battleship_gaze", 10, 30),
    RunConfig("battleship_gaze", 10, 60),
    RunConfig("battleship_gaze", 10, 120),
    RunConfig("battleship_gaze", 10, 240),
    RunConfig("tdbrain", 10, 100),
    RunConfig("tdbrain", 10, 200),
    RunConfig("tdbrain", 10, 400),
    RunConfig("tdbrain", 10, 800),
]
