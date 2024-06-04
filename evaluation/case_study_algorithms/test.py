import random
import time

import streaminghub_datamux as datamux
from fixation_detection.ivt import IVT


class SimulateStream(datamux.ManagedTask):

    t = 0.0
    dt = 1.0 / 60.0

    def __init__(self, queue: datamux.Queue) -> None:
        super().__init__()
        self.queue = queue

    def step(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=random.random(), y=random.random(), d=random.random())
        self.queue.put(item)
        time.sleep(self.dt)
        self.t += self.dt


class LogDataStream(datamux.ManagedTask):

    def __init__(self, queue: datamux.Queue) -> None:
        super().__init__()
        self.queue = queue

    def step(self, *args, **kwargs) -> None:
        try:
            item = self.queue.get(timeout=1.0)
            print(item)
        except:
            pass


if __name__ == "__main__":
    random.seed(42)
    q_points = datamux.Queue()
    q_result = datamux.Queue()
    simulator = SimulateStream(q_points)
    algorithm = IVT(
        width=1024,
        height=768,
        hertz=60,
        dist=10,
        screen=32,
        vt=200,
        q_in=q_points,
        q_out=q_result,
    )
    printer = LogDataStream(q_result)

    simulator.start()
    algorithm.start()
    printer.start()
    time.sleep(10)
    simulator.stop()
    algorithm.stop()
    printer.stop()
