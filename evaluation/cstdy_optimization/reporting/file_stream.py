import streaminghub_datamux as datamux
import pydantic
import json
import os


class FileStream(datamux.SinkTask):

    def __init__(self, *, name: str, log_dir: str, **kwargs) -> None:
        super().__init__()
        self.name = name
        self.log_dir = log_dir
        self.attrs = kwargs
        self.fp = f"{self.log_dir}/{self.name}.log"
        if os.path.exists(self.fp):
            os.remove(self.fp)

    def __call__(self, *args, **kwargs) -> None:
        item = self.source.get()
        if item is None:
            return
        print(f"[{self.name},{type(item).__name__}]", item)
        with open(self.fp, "a") as f:
            if isinstance(item, dict):
                json.dump(item, f)
            elif isinstance(item, pydantic.BaseModel):
                json.dump(item.model_dump(), f)
            f.write('\n')
