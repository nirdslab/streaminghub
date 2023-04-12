from typing import Any, Dict

from .stream import Stream


class Transform:
    inputs: Dict[str, Stream]
    outputs: Dict[str, Stream]
    uri: str

    def __init__(
        self,
        inputs: Dict[str, Stream],
        outputs: Dict[str, Stream],
        uri: str,
    ) -> None:
        self.inputs = inputs
        self.outputs = outputs
        self.uri = uri

    @staticmethod
    def create(
        data: Dict[str, Any],
    ):
        return Transform(
            inputs={k: Stream.create(v) for k, v in dict.items(data["inputs"])},
            outputs={k: Stream.create(v) for k, v in dict.items(data["outputs"])},
            uri=str(data["uri"]),
        )
