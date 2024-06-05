import logging
import random

import streaminghub_datamux as datamux
from fixation_detection import IVT
from rich.logging import RichHandler


class SimulateStream(datamux.SourceTask):

    t = 0.0
    dt = 1.0 / 60.0

    def __call__(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=random.random(), y=random.random(), d=random.random())
        self.source.put(item)
        datamux.sleep(self.dt)
        self.t += self.dt


class LogDataStream(datamux.SinkTask):

    def __call__(self, *args, **kwargs) -> None:
        try:
            item = self.source.get(timeout=1.0)
            print(f"[{type(item).__name__}]", item)
        except:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    algorithm = datamux.Pipeline(
        IVT(width=1024, height=768, hertz=60, dist=10, screen=32, vt=200),
    )
    pipeline = datamux.Pipeline(
        SimulateStream(),
        algorithm,
        LogDataStream(),
    )
    pipeline.run(duration=10)
