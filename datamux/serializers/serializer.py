import base64
import json
from typing import Tuple


class Serializer:
    def __init__(
        self,
        backend: str,
    ) -> None:
        self.backend = backend
        if self.backend == "json":
            self.encode_fn = self.__encode_json
            self.decode_fn = self.__decode_json
        elif self.backend == "avro":
            self.encode_fn = self.__encode_avro
            self.decode_fn = self.__decode_avro
        else:
            raise NotImplementedError()

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        if len(content) == 0:
            content_enc = b""
        else:
            content_enc = self.encode_fn(content)
        payload = topic + b"|" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        topic, content_enc = payload.split(b"|", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            content = self.decode_fn(content_enc)
        return topic, content

    def __encode_avro(
        self,
        content: dict,
    ) -> bytes:
        raise NotImplementedError()

    def __decode_avro(
        self,
        content_bytes: bytes,
    ) -> dict:
        raise NotImplementedError()

    def __encode_json(
        self,
        content: dict,
    ) -> bytes:
        content_str = json.dumps(content)
        content_bytes = content_str.encode()
        return content_bytes

    def __decode_json(
        self,
        content_bytes: bytes,
    ) -> dict:
        content_str = content_bytes.decode()
        content = json.loads(content_str)
        return content
