import time

from streaminghub_datamux import ManagedTask, Queue


class ProxyLiveStream(ManagedTask):

    t = 0.0
    dt = 0.1

    def step(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.queue.put(item)
        time.sleep(self.dt)
        self.t += self.dt


class LogDataStream(ManagedTask):

    def step(self, *args, **kwargs) -> None:
        try:
            item = self.queue.get(timeout=1.0)
            print(item)
        except:
            pass


if __name__ == "__main__":
    queue = Queue()
    dataloader = ProxyLiveStream(queue)
    printer = LogDataStream(queue)
    dataloader.start("pupil_core", "gaze")
    printer.start()
    time.sleep(10)
    printer.stop()
    dataloader.stop()
