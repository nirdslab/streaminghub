from typing import Dict, Any, Union

from .stream import Stream
from .pipe import Pipe

def stream_or_pipe(data: Dict[str, Any]) -> Union[Stream, Pipe]:
    if "stream" in data["$schema"]:
        return Stream.create(data)
    elif "pipe" in data["$schema"]:
        return Pipe.create(data)
    else:
        raise ValueError()