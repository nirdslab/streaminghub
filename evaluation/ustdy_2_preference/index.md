# Preference Test - Code Clarity

You are given **THREE** versions of code which passes **random data** into a **real-time algorithm**, and terminates after 10 seconds.

## Functional Style (A)

```python
import multiprocessing
import signal
import time

FREQ = 60

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
            daemon=True,
        )
        self.proc.start()
        print(f"Started {self.proc.name}")
    def stop(self):
        self.proc.terminate()
        self.proc.join()
        print(f"Stopped {self.proc.name}")

def simulate_data_stream(
    queue: multiprocessing.Queue,
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
    signal.signal(signal.SIGINT, handle_signal)
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
```

## Class Style (B)

```python
import abc
import multiprocessing
import signal
import time

FREQ = 60

class Runner:
    def __init__(self, queue):
        self.name = self.__class__.__name__
        self.queue = queue
        self.flag = False
    def __signal__(self, *args):
        self.flag = True
    def __run__(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self.__signal__)
        while not self.flag:
            self.step(*args, **kwargs)
    def start(self, *args, **kwargs):
        self.proc = multiprocessing.Process(
            group=None,
            target=self.__run__,
            name=self.name,
            args=args,
            kwargs=kwargs,
            daemon=True,
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

class SimulateStream(Runner):
    t = 0.0
    dt = 1 / FREQ
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
    simulator = SimulateStream(queue)
    printer = LogDataStream(queue)
    simulator.start()
    printer.start()
    time.sleep(10)
    printer.stop()
    simulator.stop()
```

## Using a Framework (C)

```python
import streaminghub_datamux as datamux

FREQ = 60

class SimulateStream(datamux.SourceTask):
    t = 0.0
    dt = 1.0 / FREQ
    def __call__(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.source.put(item)
        datamux.sleep(self.dt)
        self.t += self.dt

class LogDataStream(datamux.SinkTask):
    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is not None:
            print(f"[{type(item).__name__}]", item)

if __name__ == "__main__":
    pipeline = datamux.Pipeline(
        SimulateStream(),
        LogDataStream(),
    )
    pipeline.run(duration=10)
```

<aside>
💡 For the questions below, please indicate your highest to lowest preference in comma-separated form.

For example, If your preference is A > B > C, please answer as `A,B,C`.

</aside>

| # | Question | Ranking |
| --- | --- | --- |
| 1 | Which code version do you find the most readable and easy to understand? |  |
| 2 | Which code version do you believe would be the easiest to maintain and update over time? |  |
| 3 | Which code version demonstrates the best modular design? |  |
| 4 | Which code version would be the easiest to reuse in other projects or contexts? |  |
| 5 | Which code version would be the easiest to extend with additional features or functionality? |  |
| 6 | Which code version do you think would be the easiest to debug if issues arise? |  |
| 7 | Which code version do you think has the shortest learning curve for a new developer? |  |
| 8 | Which code version has the least dependency on external frameworks or libraries? |  |
| 9 | Which code version do you think has the best approach to error handling? |  |
| 10 | Taking into account all the factors above, which code version is your overall preference? |  |

If you had to migrate Code A to Code C, please rate the difficulty of this task

> **Scale : [1 = Very Low; 2 = Low; 3 = Moderate; 4 = High; 5 = Very High]**
> 

If you had to migrate Code B to Code C, please rate the difficulty of this task

> **Scale : [1 = Very Low; 2 = Low; 3 = Moderate; 4 = High; 5 = Very High]**
>