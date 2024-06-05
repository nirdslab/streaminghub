import random

import streaminghub_datamux as datamux
from fixation_detection import IVT


class SimulateStream(datamux.SourceTask):

    t = 0.0
    dt = 1.0 / 60.0

    def step(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=random.random(), y=random.random(), d=random.random())
        self.q.put(item)
        datamux.sleep(self.dt)
        self.t += self.dt


class LogDataStream(datamux.SinkTask):

    def step(self, *args, **kwargs) -> None:
        try:
            item = self.q.get(timeout=1.0)
            print(f"[{type(item).__name__}]", item)
        except:
            pass


if __name__ == "__main__":
    pipeline = datamux.Pipeline(
        SimulateStream(),
        IVT(width=1024, height=768, hertz=60, dist=10, screen=32, vt=200),
        LogDataStream(),
    )
    pipeline.run(duration=10)
