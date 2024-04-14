from typing import NamedTuple

RunConfig = NamedTuple("RunConfig", [("dataset_name", str), ("num_runs", int), ("num_points", int)])

data_config: dict = dict(
    adhd_sin=dict(
        collection_name="adhd_sin",
        stream_name="Gaze",
        attrs=dict(
            noise="0",
            participant="12",
            question="10",
        ),
    ),
    battleship_gaze=dict(
        collection_name="battleship_gaze",
        stream_name="Gaze",
        attrs=dict(
            session="1",
            stream_name="gaze",
        ),
    ),
    tdbrain=dict(
        collection_name="tdbrain",
        stream_name="eeg",
        attrs=dict(
            subject="19681349",
            session="1",
            task="restEC",
        ),
    ),
)

runs = [
    RunConfig("adhd_sin", 10, 60),
    RunConfig("adhd_sin", 10, 120),
    RunConfig("adhd_sin", 10, 240),
    RunConfig("adhd_sin", 10, 480),
    RunConfig("battleship_gaze", 10, 30),
    RunConfig("battleship_gaze", 10, 60),
    RunConfig("battleship_gaze", 10, 120),
    RunConfig("battleship_gaze", 10, 240),
    RunConfig("tdbrain", 10, 100),
    RunConfig("tdbrain", 10, 200),
    RunConfig("tdbrain", 10, 400),
    RunConfig("tdbrain", 10, 800),
]
