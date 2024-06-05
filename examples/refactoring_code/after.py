import streaminghub_datamux as datamux


class SimulateStream(datamux.SourceTask):

    t = 0.0
    dt = 1.0 / 60.0

    def step(self, *args, **kwargs) -> None:
        item = dict(t=self.t, x=0, y=0, d=0)
        self.q.put(item)
        datamux.sleep(self.dt)
        self.t += self.dt


class LogDataStream(datamux.SinkTask):

    def step(self, *args, **kwargs) -> None:
        try:
            item = self.q.get(timeout=1.0)
            print(f"[{type(item).__name__}]", item)
        except:
            pass


if __name__ == "__main__":
    pipeline = datamux.Pipeline(
        SimulateStream(),
        LogDataStream(),
    )
    pipeline.run(duration=10)