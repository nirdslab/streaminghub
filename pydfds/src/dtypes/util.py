from typing import Any, Dict, Union

from .pipe import Pipe
from .stream import Stream


def stream_or_pipe(data: Dict[str, Any]) -> Union[Stream, Pipe]:
    if not "$schema" in data:
        raise ValueError("missing key: '$schema'")
    if "stream" in data["$schema"]:
        return Stream.create(data)
    if "pipe" in data["$schema"]:
        return Pipe.create(data)
    raise ValueError("unknown value: '$schema'")