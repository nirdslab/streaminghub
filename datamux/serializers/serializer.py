from typing import Tuple

class Serializer:
    """
    Serialization Base Class for DataMux

    """

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        raise NotImplementedError()

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        raise NotImplementedError()

    def bind_schema(
        self,
        topic: bytes,
        schema: dict,
    ) -> None:
        pass

    @staticmethod
    def for_backend(
        backend: str,
    ):
        if backend == "json":
            from .json import JSONSerializer
            return JSONSerializer()
        if backend == "avro":
            from .avro import AvroSerializer
            return AvroSerializer()
        raise NotImplementedError()
