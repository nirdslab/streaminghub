from typing import List


class DeviceDesc:
    name: str
    device_type: str

    def __init__(self, name: str, device_type: str) -> None:
        super().__init__()
        self.name = name
        self.device_type = device_type


class StreamDesc:
    name: str
    unit: str
    freq: int
    channel_count: int
    channels: List[str]

    def __init__(self, name: str, unit: str, freq: int, channel_count: int, channels: List[str]) -> None:
        super().__init__()
        self.name = name
        self.unit = unit
        self.freq = freq
        self.channel_count = channel_count
        self.channels = channels
