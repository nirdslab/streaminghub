import json
from pathlib import Path

from .typing import Config

config_paths = [
    Path("~/.streaminghubrc").expanduser().resolve(),
    Path(".streaminghubrc").resolve(),
]


def load_config() -> Config:
    data = {}
    for path in config_paths:
        if path.exists() and path.is_file():
            with open(path) as f:
                patch = json.load(f)
                data.update(patch)
    config = Config(**data)
    return config


def write_config(config: Config):
    # update the highest priority file
    path = config_paths[-1]
    with open(path, "w") as f:
        json.dump(config.model_dump(), f)
