from __future__ import annotations

import copy
import signal
from typing import Literal
from argparse import Namespace

import streaminghub_datamux as dm


class CompositeTask(dm.ITask):

    tasks: tuple[dm.ITask, ...]

    def __init__(self, *tasks: dm.ITask, run_self=False, transform=None) -> None:
        # start composite task on a thread, not a process.
        # internal tasks will still be processes
        super().__init__(mode="thread")
        assert len(tasks) > 0
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
    completed: dm.Flag

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
            self.completed.set()
            return 0


class MergedSource(CompositeTask):
    """
    Merge multiple data sources together

    """

    target: dm.Queue

    def __init__(
        self,
        t1: dm.SourceTask | Pipeline,
        t2: dm.SourceTask | Pipeline,
        *tn: dm.SourceTask | Pipeline,
        agg: Literal["list", "dict", "obj"] = "obj",
        transform=None,
    ) -> None:
        # expect at least two tasks to merge
        super().__init__(t1, t2, *tn, run_self=True)
        self.target = dm.Queue(timeout=0.001)
        self.sync_state: list[None | dict] = [None] * len(self.tasks)
        self.agg = agg
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

        # prepare output based on given agg
        if self.agg == "list":
            output = copy.deepcopy(self.sync_state)
        elif self.agg == "dict":
            output = {}
            for i, task in enumerate(self.tasks):
                state = self.sync_state[i]
                if state is not None:
                    output[task.name] = dict(**state)
        elif self.agg == "obj":
            output = Namespace(**{task.name: None for task in self.tasks})
            for i, task in enumerate(self.tasks):
                state = self.sync_state[i]
                if state is not None:
                    setattr(output, task.name, Namespace(**state))
        if self.transform is not None:
            output = self.transform(output)

        self.target.put(output)


class Pipeline(CompositeTask):

    # data source for the pipeline. if pipeline begins with source, its assigned automatically
    source: dm.Queue

    # output of the pipeline
    target: dm.Queue

    # flag to check for completion
    completed: dm.Flag

    def __init__(self, *tasks: dm.ITask) -> None:
        super().__init__(*tasks, run_self=False)

        # handle first task
        first = self.tasks[0]
        if isinstance(first, (dm.SourceTask, MergedSource)):
            self.source = None  # type: ignore
            self.target = first.target
            self.logger.info(f"task={first.name}, source=None, target={first.target}")
        elif isinstance(first, (dm.PipeTask, dm.Pipeline)):
            self.source = first.source
            self.target = first.target
        else:
            raise ValueError(first)

        # handle intermediate tasks
        for task in self.tasks[1:-1]:
            assert isinstance(task, (dm.PipeTask, Pipeline))
            task.source.assign(self.target)
            self.target = task.target
            self.logger.info(f"task={task.name}, source={task.source}, target={task.target}")

        # handle last task
        last = self.tasks[-1]
        if first == last:
            pass
        elif isinstance(last, Pipeline):
            last.source.assign(self.target)
            self.target = last.target
            self.completed = last.completed
            self.logger.info(f"task={last.name}, source={last.source}, target={last.target}")
        elif isinstance(last, (dm.SinkTask, Broadcast)):
            # print(self.target.q)
            last.source.assign(self.target)
            self.target = None  # type: ignore
            self.completed = last.completed
            self.logger.info(f"task={last.name}, source={last.source}, target=None")
        else:
            raise ValueError(last)

    def run(self, duration: float | None = None) -> None:
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

    def __call__(self, msg: dict | Namespace):
        if msg == dm.END_OF_STREAM:
            return msg
        target = {}
        if isinstance(msg, dict):
            for k, expr in self.mapping.items():
                target[k] = eval(expr, {**msg, **msg.get("index", {}), **msg.get("value", {})})
        elif isinstance(msg, Namespace):
            for k, expr in self.mapping.items():
                target[k] = eval(expr, dict(msg._get_kwargs()))
        return target


class Filter(dm.PipeTask):

    def __init__(self, condition: str) -> None:
        super().__init__(transform=None)
        self.condition = condition

    def close(self) -> None:
        pass

    def step(self, item) -> int | None:
        check = eval(self.condition, item)
        if check == True:
            self.target.put(item)
