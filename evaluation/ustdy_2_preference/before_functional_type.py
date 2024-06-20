import multiprocessing
import signal
import time


class Runner:

    def __init__(self, func, queue):
        self.func = func
        self.queue = queue

    def start(self, *args, **kwargs):
        self.proc = multiprocessing.Process(
            group=None,
            target=self.func,
            name=self.func.__name__,
            args=args,
            kwargs=dict(**kwargs, queue=queue),
            daemon=False,
        )
        self.proc.start()
        print(f"Started {self.proc.name}")

    def stop(self):
        self.proc.terminate()
        self.proc.join()
        print(f"Stopped {self.proc.name}")


def simulate_data_stream(
    source_id: str,
    stream_id: str,
    queue: multiprocessing.Queue,
):
    print(source_id, stream_id)
    flag = False
    t = 0.0
    dt = 1.0 / 60.0

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

    signal.signal(signal.SIGTERM, handle_signal)
    while not flag:
        step()


def log_data_stream(
    queue: multiprocessing.Queue,
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

    signal.signal(signal.SIGTERM, handle_signal)
    while not flag:
        step()


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    simulator = Runner(simulate_data_stream, queue)
    printer = Runner(log_data_stream, queue)
    simulator.start()
    printer.start()
    time.sleep(10)
    printer.stop()
    simulator.stop()
