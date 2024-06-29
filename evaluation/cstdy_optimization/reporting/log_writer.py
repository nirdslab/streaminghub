import streaminghub_datamux as datamux


class LogWriter(datamux.SinkTask):

    def __init__(self, *, name: str, **kwargs) -> None:
        super().__init__()
        self.name = name
        self.attrs = kwargs

    def __call__(self, *args, **kwargs) -> int | None:
        item = self.source.get()
        if item is None:
            return
        print(f"[{self.name},{type(item).__name__}]", item)
        if item == datamux.END_OF_STREAM:
            self.logger.warning(f"reached end of stream")
            self.completed.set()
            return 0
