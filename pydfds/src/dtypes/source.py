from typing import Any, Dict, Optional

from .device import Device
from .stream import Stream


class Source:
    streams: Dict[str, Stream]
    device: Optional[Device]

    def __init__(
        self,
        streams: Dict[str, Stream],
        device: Optional[Device],
    ) -> None:
        self.streams = streams
        self.device = device

    @staticmethod
    def create(
        data: Dict[str, Any],
    ):
        return Source(
            streams={k: Stream.create(v) for k, v in dict.items(data["streams"])},
            device=Device.create(data.get("device", None)),
        )
