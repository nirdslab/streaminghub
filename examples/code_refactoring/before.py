import multiprocessing
import time
from threading import Thread


class Flag:

    _up = True

    def up(self):
        self._up = True

    def down(self):
        self._up = False

    def is_up(self):
        return self._up == True

    def is_down(self):
        return self._up == False


def start_pupil_labs_stream(
    source_id: str,
    stream_id: str,
    queue: multiprocessing.Queue,
    flag: Flag,
):
    print(source_id, stream_id)
    t, dt = 0.0, 0.1  # sampling frequency = 10 Hz
    while flag.is_up():
        # add mock data to queue
        item = dict(t=t, x=0, y=0, d=0)
        queue.put(item)
        print(item)
        time.sleep(dt)
        t += dt


class Driver:

    def __init__(self, func, name, queue):
        self.flag = Flag()
        self.func = func
        self.name = name
        self.queue = queue

    def start(self, *args, **kwargs):
        self.flag.up()
        self.task = Thread(
            group=None,
            target=self.func,
            name=self.name,
            args=(*args, self.queue, self.flag),
            kwargs=kwargs,
            daemon=False,
        )
        self.task.start()
        print("Started stream -> queue")

    def stop(self):
        self.flag.down()
        self.task.join()
        print("Ended stream -> queue")


if __name__ == "__main__":
    queue = multiprocessing.Queue()
    driver = Driver(
        func=start_pupil_labs_stream,
        name="pupil_labs_test_driver",
        queue=queue,
    )
    source_id = "pupil_core"
    stream_id = "gaze"
    driver.start(source_id, stream_id)
    time.sleep(10)
    driver.stop()
