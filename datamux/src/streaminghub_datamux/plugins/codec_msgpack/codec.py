import logging

import msgpack
from pydantic_core import to_jsonable_python
from streaminghub_datamux.rpc import RpcCodec, to_serializable


class MsgpackCodec(RpcCodec):
    """
    Msgpack Codec for StreamingHub DataMux

    """

    logger = logging.getLogger(__name__)

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        self.logger.debug(f"encode(): topic={topic}, content={content}")
        if len(content) == 0:
            content_enc: bytes = b""
        else:
            try:
                content_enc = msgpack.dumps(to_jsonable_python(content, fallback=to_serializable))  # type: ignore
            except Exception as e:
                self.logger.error(f"topic={topic},content={content} cannot be msgpack-encoded")
                raise e
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
            content = dict(msgpack.loads(content_enc))  # type: ignore
        return topic, content
