from __future__ import annotations

import copy
import signal
from typing import Literal

import streaminghub_datamux as dm


class CompositeTask(dm.ITask):

    tasks: tuple[dm.ITask, ...]

    def __init__(self, *tasks: dm.ITask, run_self=False, transform=None) -> None:
        # start composite task on a thread, not a process.
        # internal tasks will still be processes
        super().__init__(mode="thread")
        self.tasks = tasks
        self.run_self = run_self
        self.transform = transform

    def start(self):
        signal.signal(signal.SIGINT, self.__signal__)
        if self.run_self:
            super().start()
        for task in self.tasks:
            task.start()

    def stop(self):
        if self.run_self:
            super().stop()
        for task in self.tasks:
            task.stop()

    def __signal__(self, *args):
        self.stop()
        signal.default_int_handler(*args)


class Broadcast(CompositeTask):

    source: dm.Queue

    def __init__(self, *tasks: dm.PipeTask | dm.SinkTask) -> None:
        super().__init__(*tasks, run_self=True)
        self.source = dm.Queue(timeout=0.001, empty=True)

    def __call__(self, *args, **kwargs) -> int | None:
        item = self.source.get()
        if item is None:
            return
        # broadcast source item to all task queues
        for task in self.tasks:
            assert isinstance(task, (dm.PipeTask, dm.SinkTask, dm.Pipeline))
            task.source.put(copy.deepcopy(item))
        if item == dm.END_OF_STREAM:
            return 0


class MergedSource(CompositeTask):
    """
    Merge multiple data sources together

    """

    target: dm.Queue

    def __init__(
        self,
        t1: dm.SourceTask,
        t2: dm.SourceTask,
        *tn: dm.SourceTask,
        dtype: Literal["list", "dict"] = "list",
        transform=None,
    ) -> None:
        # expect at least two tasks to merge
        super().__init__(t1, t2, *tn, run_self=True)
        self.target = dm.Queue(timeout=0.001)
        self.sync_state = [None] * len(self.tasks)
        self.dtype = dtype
        self.transform = transform

    def __call__(self, *args, **kwargs) -> int | None:
        changed = False
        for i, task in enumerate(self.tasks):
            assert isinstance(task, dm.ITaskWithOutput)
            item = task.target.get()
            if item is None:
                continue
            changed = True
            self.sync_state[i] = item
        if not changed:
            return
        # put combined output into target queue
        if all([x == dm.END_OF_STREAM for x in self.sync_state]):
            self.target.put(dm.END_OF_STREAM)
            return 0

        # prepare output based on given dtype
        if self.dtype == "list":
            output = copy.deepcopy(self.sync_state)
        elif self.dtype == "dict":
            output = {}
            for i, task in enumerate(self.tasks):
                output[task.name] = copy.deepcopy(self.sync_state[i])

        if self.transform is not None:
            output = self.transform(output)
        
        self.target.put(output)


class Pipeline(CompositeTask):

    source: dm.Queue
    target: dm.Queue
    completed: dm.Flag

    def __init__(self, *tasks: dm.ITask) -> None:
        super().__init__(*tasks, run_self=False)
        for i, task in enumerate(self.tasks):
            if isinstance(task, (dm.SourceTask, MergedSource)):
                assert i == 0
                q = task.target
                self.logger.debug(f"task={task.name}, source=None, target={task.target}")
            elif isinstance(task, dm.SinkTask):
                assert i == len(self.tasks) - 1
                task.source = q
                self.completed = task.completed
                self.logger.debug(f"task={task.name}, source={task.source}, target=None")
            elif isinstance(task, dm.PipeTask):
                if i == 0:
                    # source is empty
                    task.source = dm.Queue(empty=True)
                    q = task.target
                    self.logger.debug(f"task={task.name}, source={task.source}, target={task.target}")
                else:
                    # source is non-empty
                    task.source = q
                    q = task.target
                    self.logger.debug(f"task={task.name}, source={task.source}, target={task.target}")
            elif isinstance(task, Pipeline):
                assert i > 0
                # source is non-empty
                assert q is not None
                task.source.assign(q)
                q = task.target
                self.logger.debug(f"task={task.name}, source={task.source}, target={task.target}")
        self.target = q

    def run(self, duration: float | None = None):
        self.start()
        self.logger.info("pipeline started")
        try:
            self.completed.wait(duration)
            self.logger.info("pipeline completed")
        except BaseException as e:
            self.logger.warning(f"pipeline raised an exception: {e}")
            raise e
        self.stop()

    def __call__(self, *args, **kwargs) -> None:
        raise ValueError("should never be called")


class ExpressionMap:

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def __call__(self, msg: dict):
        if msg == dm.END_OF_STREAM:
            return msg
        target = {}
        for k, expr in self.mapping.items():
            target[k] = eval(expr, {**msg, **msg.get("index", {}), **msg.get("value", {})})
        return target
