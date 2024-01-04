import json
from pathlib import Path

from .typing import Config


def load_config() -> Config:
    config_path = Path("~/.streaminghubrc").expanduser().resolve()
    assert config_path.exists() and config_path.is_file()
    with open(config_path) as f:
        data = json.load(f)
    config = Config(**data)
    return config
