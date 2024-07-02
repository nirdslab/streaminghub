from __future__ import annotations

import signal

import streaminghub_datamux as dm


class CompositeTask(dm.ITask):

    tasks: tuple[dm.ITask, ...]

    def __init__(self, *tasks: dm.ITask, run_self=False) -> None:
        super().__init__(mode="thread")
        self.run_self = run_self
        self.tasks = tasks

    def start(self):
        signal.signal(signal.SIGINT, self.__signal__)
        if self.run_self:
            # don't start new process for composition constructs
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

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        # broadcast source item to all task queues
        for task in self.tasks:
            assert isinstance(task, (dm.PipeTask, dm.SinkTask, dm.Pipeline))
            task.source.put(item)


class SyncSource(CompositeTask):

    target: dm.Queue

    def __init__(self, *tasks: dm.SourceTask) -> None:
        super().__init__(*tasks, run_self=True)
        self.target = dm.Queue(timeout=0.001)
        self.last_task_states = [None] * len(self.tasks)

    def __call__(self, *args, **kwargs) -> None:
        received_any = False
        for i, task in enumerate(self.tasks):
            assert isinstance(task, dm.ITaskWithOutput)
            item = task.target.get()
            if item is not None:
                self.last_task_states[i] = item
                received_any = True
        # put combined output into target queue
        if received_any:
            self.target.put(self.last_task_states)


class Pipeline(CompositeTask):

    source: dm.Queue
    target: dm.Queue
    completed: dm.Flag

    def __init__(self, *tasks: dm.ITask) -> None:
        super().__init__(*tasks, run_self=False)
        for i, task in enumerate(self.tasks):
            if isinstance(task, (dm.SourceTask, SyncSource)):
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
        index, value = msg["index"], msg["value"]
        target = {}
        for k, expr in self.mapping.items():
            target[k] = eval(expr, {**index, **value})
        return target
