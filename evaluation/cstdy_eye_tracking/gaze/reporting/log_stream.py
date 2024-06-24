import streaminghub_datamux as datamux


class LogStream(datamux.SinkTask):

    def __init__(self, *, name: str, **kwargs) -> None:
        super().__init__()
        self.name = name
        self.attrs = kwargs

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        print(f"[{self.name},{type(item).__name__}]", item)
