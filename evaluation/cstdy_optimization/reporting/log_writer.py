import streaminghub_datamux as dm


class LogWriter(dm.SinkTask):

    def __init__(self, *, name: str, **kwargs) -> None:
        super().__init__()
        self.name = name
        self.attrs = kwargs

    def step(self, item) -> int | None:
        print(f"[{self.name},{type(item).__name__}]", item)
