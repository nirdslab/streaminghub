from typing import Dict, Optional

from .device import Device
from .stream import Stream


class Node:
    device: Optional[Device]
    uri: Optional[str]
    inputs: Dict[str, Stream]
    outputs: Dict[str, Stream]

    def __init__(
        self,
        device: Optional[Device],
        uri: Optional[str],
        inputs: Dict[str, Stream],
        outputs: Dict[str, Stream],
    ) -> None:
        self.device = device
        self.uri = uri
        self.inputs = inputs
        self.outputs = outputs
