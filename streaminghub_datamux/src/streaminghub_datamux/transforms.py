import streaminghub_datamux as dm


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


class Broadcast(dm.ITaskWithSource):
    targets: list[dm.ITaskWithSource]

    def __init__(self, *tasks: dm.SourceTask | dm.SinkTask | dm.PipeTask | dm.Pipeline) -> None:
        super().__init__()
        self.source = dm.Queue(timeout=0.001, empty=True)
        self.tasks = tasks

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        for target in self.targets:
            target.source.put_nowait(item)


class Sync(dm.PipeTask):

    target: dm.Queue

    def __init__(self, *tasks: dm.PipeTask) -> None:
        super().__init__()
        self.tasks = tasks

    def __call__(self, *args, **kwargs) -> None:
        for task in self.tasks:
            item = task.target.get()
            if item is not None:
                self.target.put_nowait(item)
