import logging

import streaminghub_datamux as datamux
from gaze.fixation_detection import IVT
from gaze.output import LogDataStream
from gaze.synthesis import PinkNoiseSimulator, UniformNoiseSimulator, WhiteNoiseSimulator
from rich.logging import RichHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

    # uniform noise simulator
    pipeline = datamux.Pipeline(
        UniformNoiseSimulator(),
        LogDataStream(),
    )
    pipeline.run(duration=10)

    # uniform noise simulator -> fixation/saccade -> white noise simulator
    pipeline = datamux.Pipeline(
        UniformNoiseSimulator(),
        IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100),
        WhiteNoiseSimulator(),
        LogDataStream(),
    )
    pipeline.run(duration=10)

    # # uniform noise simulator -> fixation/saccade -> pink noise simulator
    pipeline = datamux.Pipeline(
        UniformNoiseSimulator(),
        IVT(width=1, height=1, hertz=60, dist=1, screen=1, vt=100),
        PinkNoiseSimulator(),
        LogDataStream(),
    )
    pipeline.run(duration=10)

    # TODO run on [N_BACK, ADHD_SIN] again and save results
