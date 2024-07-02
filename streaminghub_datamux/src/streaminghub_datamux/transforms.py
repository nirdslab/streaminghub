from __future__ import annotations

import signal

import streaminghub_datamux as dm


class CompositeTask(dm.ITask):

    tasks: tuple[dm.ITask, ...]

    def __init__(self, *tasks: dm.ITask) -> None:
        super().__init__()
        self.tasks = tasks

    def start(self):
        signal.signal(signal.SIGINT, self.__signal__)
        for task in self.tasks:
            task.start()

    def stop(self):
        for task in self.tasks:
            task.stop()

    def __signal__(self, *args):
        self.stop()
        signal.default_int_handler(*args)


class Pipeline(CompositeTask):

    target: dm.Queue

    @property
    def source(self) -> dm.Queue:
        # ensure the first task has a source
        assert isinstance(self.tasks[0], dm.ITaskWithOutput)
        return self.tasks[0].target

    def __init__(self, *tasks: dm.ITask) -> None:
        super().__init__(*tasks)
        for i, task in enumerate(self.tasks):
            if isinstance(task, dm.SourceTask):
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


class Broadcast(CompositeTask):
    targets: list[dm.ITaskWithOutput]

    def __init__(self, *tasks: dm.PipeTask) -> None:
        super().__init__()
        self.source = dm.Queue(timeout=0.001, empty=True)
        self.tasks = tasks

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        for target in self.targets:
            target.target.put(item)


class Sync(CompositeTask):

    target: dm.Queue

    def __init__(self, *tasks: dm.ITaskWithOutput) -> None:
        super().__init__()
        self.tasks = tasks
        self.last_task_states = [None] * len(self.tasks)

    def __call__(self, *args, **kwargs) -> None:
        for i, task in enumerate(self.tasks):
            assert isinstance(task, dm.ITaskWithOutput)
            item = task.target.get()
            if item is not None:
                self.last_task_states[i] = item
        # return combined output
        self.target.put(self.last_task_states)


class ExpressionMap:

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def __call__(self, msg: dict):
        if msg == dm.END_OF_STREAM:
            return msg
        index, value = msg["index"], msg["value"]
        target = {}
        for k, expr in self.mapping.items():
            target[k] = eval(expr, {**index, **value})
        return target
