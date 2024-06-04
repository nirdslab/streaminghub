import time

from streaminghub_datamux import ManagedTask, Queue


class SimulateStream(ManagedTask):

    t = 0.0
    dt = 1.0 / 60.0

    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue

    def step(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.queue.put(item)
        time.sleep(self.dt)
        self.t += self.dt


class LogDataStream(ManagedTask):

    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue

    def step(self, *args, **kwargs) -> None:
        item = self.queue.get()
        print(item)


if __name__ == "__main__":
    queue = Queue()
    simulator = SimulateStream(queue)
    printer = LogDataStream(queue)
    simulator.start()
    printer.start()
    time.sleep(10)
    printer.stop()
    simulator.stop()
