import streaminghub_datamux as datamux


class LogDataStream(datamux.SinkTask):

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        print(f"[{type(item).__name__}]", item)
