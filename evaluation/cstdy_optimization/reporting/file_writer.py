import json
import os

import pydantic

import streaminghub_datamux as datamux


class FileWriter(datamux.SinkTask):

    def __init__(self, *, name: str, log_dir: str, **kwargs) -> None:
        super().__init__()
        self.name = f"{self.__class__.__name__}"
        self.filename = name
        self.log_dir = log_dir
        self.attrs = kwargs
        self.fp = f"{self.log_dir}/{self.filename}.log"
        os.makedirs(log_dir, exist_ok=True)
        if os.path.exists(self.fp):
            os.remove(self.fp)
        self.logger.info(f"File: {self.fp}")

    def step(self, item) -> int | None:
        with open(self.fp, "a") as f:
            if isinstance(item, dict):
                json.dump(item, f)
            elif isinstance(item, pydantic.BaseModel):
                json.dump(item.model_dump(), f)
            f.write("\n")
