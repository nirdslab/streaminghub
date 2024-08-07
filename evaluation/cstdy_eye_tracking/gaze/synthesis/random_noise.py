import random

import streaminghub_datamux as dm


class UniformNoiseSimulator(dm.SourceTask):

    def __init__(self, t_start: float = 0.0, freq: float = 60.0) -> None:
        super().__init__()
        self.t = t_start
        self.dt = 1.0 / freq

    def __call__(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=random.random(), y=random.random(), d=random.random())
        self.target.put(item)
        dm.sleep(self.dt)
        self.t += self.dt
