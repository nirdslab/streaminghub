import multiprocessing
import signal
import time


def proxy_pupil_core_stream(
    source_id: str,
    stream_id: str,
    queue: multiprocessing.Queue,
):
    print(source_id, stream_id)
    run = True

    def handle_signal(signum, frame):
        nonlocal run
        run = False

    signal.signal(signal.SIGTERM, handle_signal)

    t, dt = 0.0, 0.1  # sampling frequency = 10 Hz
    while run:
        # add mock data to queue
        item = dict(t=t, x=0, y=0, d=0)
        queue.put(item)
        time.sleep(dt)
        t += dt


def log_data_stream(
    queue: multiprocessing.Queue,
):
    run = True

    def handle_signal(signum, frame):
        nonlocal run
        run = False

    signal.signal(signal.SIGTERM, handle_signal)

    while run:
        try:
            item = queue.get(timeout=1.0)
            print(item)
        except:
            continue


class Runner:

    def __init__(self, func, name, queue):
        self.func = func
        self.name = name
        self.queue = queue

    def start(self, *args, **kwargs):
        self.task = multiprocessing.Process(
            group=None,
            target=self.func,
            name=self.name,
            args=(*args, self.queue),
            kwargs=kwargs,
            daemon=False,
        )
        self.task.start()
        print(f"Started {self.name}")

    def stop(self):
        self.task.terminate()
        self.task.join()
        print(f"Stopped {self.name}")


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    dataloader = Runner(
        func=proxy_pupil_core_stream,
        name="pupil_core_proxy",
        queue=queue,
    )
    printer = Runner(
        func=log_data_stream,
        name="stream_logger",
        queue=queue,
    )
    source_id = "pupil_core"
    stream_id = "gaze"
    dataloader.start(source_id, stream_id)
    printer.start()
    time.sleep(10)
    printer.stop()
    dataloader.stop()
