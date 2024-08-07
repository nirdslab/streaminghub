import multiprocess
import signal
import time

FREQ = 60


class Runner:

    def __init__(self, func, queue):
        self.func = func
        self.queue = queue

    def start(self, *args, **kwargs):
        self.proc = multiprocess.Process(
            group=None,
            target=self.func,
            name=self.func.__name__,
            args=args,
            kwargs=dict(**kwargs, queue=queue),
            daemon=True,
        )
        self.proc.start()
        print(f"Started {self.proc.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        print(f"Stopped {self.proc.name}")


def simulate_data_stream(
    queue: multiprocess.Queue,
):
    flag = False
    t = 0.0
    dt = 1 / FREQ

    def handle_signal(signum, frame):
        nonlocal flag
        flag = True

    def step():
        nonlocal t
        # add mock data to queue
        item = dict(t=t, x=0, y=0, d=0)
        queue.put(item)
        time.sleep(dt)
        t += dt

    signal.signal(signal.SIGINT, handle_signal)
    while not flag:
        step()


def log_data_stream(
    queue: multiprocess.Queue,
):
    flag = False

    def handle_signal(signum, frame):
        nonlocal flag
        flag = True

    def step():
        try:
            item = queue.get(timeout=1.0)
            print(item)
        except:
            pass

    signal.signal(signal.SIGINT, handle_signal)
    while not flag:
        step()


if __name__ == "__main__":
    queue = multiprocess.Queue()
    simulator = Runner(simulate_data_stream, queue)
    printer = Runner(log_data_stream, queue)
    simulator.start()
    printer.start()
    time.sleep(10)
    printer.stop()
    simulator.stop()
