import streaminghub_datamux as dm

FREQ = 60


class SimulateStream(dm.SourceTask):

    t = 0.0
    dt = 1.0 / FREQ

    def __call__(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.target.put(item)
        dm.sleep(self.dt)
        self.t += self.dt


class LogDataStream(dm.SinkTask):

    def step(self, item) -> int | None:
        print(f"[{type(item).__name__}]", item)


if __name__ == "__main__":
    pipeline = dm.Pipeline(
        SimulateStream(),
        LogDataStream(),
    )
    pipeline.run(duration=10)
