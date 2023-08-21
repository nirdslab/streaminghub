import json
import logging
from typing import Tuple
from .serializer import Serializer


class JSONSerializer(Serializer):
    """
    Serialization Utilty for DataMux

    """

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        logging.info(f"encode(): topic={topic}, content={content}")
        if len(content) == 0:
            content_enc = b""
        else:
            content_str = json.dumps(content)
            content_enc = content_str.encode()
        payload = topic + b"||" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        logging.info(f"decode(): payload={payload}")
        topic, content_enc = payload.split(b"||", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            content_str = content_enc.decode()
            content = json.loads(content_str)
        return topic, content
