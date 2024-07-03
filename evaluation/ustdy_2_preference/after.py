import streaminghub_datamux as datamux

FREQ = 60


class SimulateStream(datamux.SourceTask):

    t = 0.0
    dt = 1.0 / FREQ

    def __call__(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.target.put(item)
        datamux.sleep(self.dt)
        self.t += self.dt


class LogDataStream(datamux.SinkTask):

    def step(self, item) -> int | None:
        print(f"[{type(item).__name__}]", item)


if __name__ == "__main__":
    pipeline = datamux.Pipeline(
        SimulateStream(),
        LogDataStream(),
    )
    pipeline.run(duration=10)
