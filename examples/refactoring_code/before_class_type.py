import abc
import multiprocessing
import signal
import time


class Runner:

    def __init__(self, queue):
        self.name = self.__class__.__name__
        self.queue = queue
        self.flag = False

    def __signal__(self, *args):
        self.flag = True

    def __run__(self, *args, **kwargs):
        signal.signal(signal.SIGTERM, self.__signal__)
        while not self.flag:
            self.step(*args, **kwargs)

    def start(self, *args, **kwargs):
        self.proc = multiprocessing.Process(
            group=None,
            target=self.__run__,
            name=self.name,
            args=args,
            kwargs=kwargs,
            daemon=False,
        )
        self.proc.start()
        print(f"Started {self.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        print(f"Stopped {self.name}")

    @abc.abstractmethod
    def step(self):
        raise NotImplementedError()


class ProxyPupilCore(Runner):

    t = 0.0
    dt = 0.1

    def step(self, *args, **kwargs):
        item = dict(t=self.t, x=0, y=0, d=0)
        self.queue.put(item)
        time.sleep(self.dt)
        self.t += self.dt


class LogDataStream(Runner):

    def step(self, *args, **kwargs):
        try:
            item = self.queue.get(timeout=1.0)
            print(item)
        except:
            pass


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    dataloader = ProxyPupilCore(queue)
    printer = LogDataStream(queue)
    dataloader.start("pupil_core", "gaze")
    printer.start()
    time.sleep(10)
    printer.stop()
    dataloader.stop()
