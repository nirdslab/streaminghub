import base64
import json

import numpy as np
from dfds.typing import Stream


class Serializer:
    def __init__(
        self,
        backend: str,
    ) -> None:
        self.backend = backend

    def encode(
        self,
        topic: str,
        **kwargs,
    ) -> dict:
        if self.backend == "json":
            return {"topic": topic, "content": self.encode_json(**kwargs)}
        elif self.backend == "avro":
            return {"topic": topic, "content": self.encode_avro(**kwargs)}
        else:
            raise NotImplementedError()

    def encode_avro(
        self,
        **kwargs,
    ) -> bytes:
        raise NotImplementedError()

    def encode_json(
        self,
        **kwargs,
    ) -> bytes:
        assert "stream" in kwargs
        assert "index" in kwargs
        assert "value" in kwargs

        stream = kwargs["stream"]
        index = kwargs["index"]
        value = kwargs["value"]

        assert isinstance(stream, Stream)
        assert isinstance(index, np.ndarray)
        assert isinstance(value, np.ndarray)

        payload = {
            "stream": stream.dict(),
            "index": index.tolist(),
            "value": value.tolist(),
        }
        payload_bytes = json.dumps(payload).encode()
        return base64.encodebytes(payload_bytes)
