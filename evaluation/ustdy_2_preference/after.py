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

    def __call__(self, *args, **kwargs) -> int | None:
        item = self.source.get()
        if item == datamux.END_OF_STREAM:
            self.logger.debug("got EOF token")
            self.completed.set()
            self.logger.debug("set EOF flag")
            return 0
        if item is None:
            return
        
        print(f"[{type(item).__name__}]", item)


if __name__ == "__main__":
    pipeline = datamux.Pipeline(
        SimulateStream(),
        LogDataStream(),
    )
    pipeline.run(duration=10)
