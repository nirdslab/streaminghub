import json
import logging

from pydantic_core import to_jsonable_python
from streaminghub_datamux.rpc import RpcCodec, to_serializable


class JSONCodec(RpcCodec):
    """
    JSON Codec for StreamingHub DataMux

    """

    logger = logging.getLogger(__name__)

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        self.logger.debug(f"encode(): topic={topic}, content={content}")
        if len(content) == 0:
            content_enc = b""
        else:
            try:
                content_str = json.dumps(to_jsonable_python(content, fallback=to_serializable))
            except Exception as e:
                self.logger.error(f"topic={topic},content={content} cannot be JSON encoded")
                raise e
            content_enc = content_str.encode()
        payload = topic + b"||" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> tuple[bytes, dict]:
        self.logger.debug(f"decode(): payload={payload}")
        topic, content_enc = payload.split(b"||", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            content_str = content_enc.decode()
            content = json.loads(content_str)
        return topic, content
