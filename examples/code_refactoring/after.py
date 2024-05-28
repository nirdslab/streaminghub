import time

from streaminghub_datamux import ManagedTask, Queue


class ProxyLiveStream(ManagedTask):

    def __init__(self, queue: Queue, t=0.0, dt=0.1) -> None:
        super().__init__(queue)
        self.t = t
        self.dt = dt

    def step(self) -> None:
        # add mock data to queue
        item = dict(t=self.t, x=0, y=0, d=0)
        self.queue.put(item)
        time.sleep(self.dt)
        self.t += self.dt


class LogDataStream(ManagedTask):

    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)

    def step(self) -> None:
        try:
            item = self.queue.get(timeout=1.0)
            print(item)
        except:
            pass


if __name__ == "__main__":
    queue = Queue()
    dataloader = ProxyLiveStream(queue)
    printer = LogDataStream(queue)
    source_id = "pupil_core"
    stream_id = "gaze"
    dataloader.start(source_id, stream_id)
    printer.start()
    time.sleep(10)
    printer.stop()
    dataloader.stop()
