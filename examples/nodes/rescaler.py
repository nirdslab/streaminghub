import streaminghub_datamux as dm


class Rescaler(dm.PipeTask):

    def __init__(self, μx=0.0, μy=0.0, σx=1.0, σy=1.0, transform=None) -> None:
        super().__init__(mode="process", transform=transform)
        self.μx = μx
        self.μy = μy
        self.σx = σx
        self.σy = σy

    def step(self, input) -> int | None:
        t, x, y = input["t"], input["x"], input["y"]
        output = dict(
            t=t,
            x=(x - self.μx) / self.σx,
            y=(y - self.μy) / self.σy,
        )
        self.target.put(output)

    def close(self) -> None:
        pass
