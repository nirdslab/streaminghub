from typing import Tuple

class Serializer:
    """
    Serialization Base Class for DataMux

    """

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes | list[bytes]:
        raise NotImplementedError()

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict] | None:
        raise NotImplementedError()

    @staticmethod
    def with_backend(
        backend: str,
    ):
        if backend == "json":
            from .json import JSONSerializer
            return JSONSerializer()
        if backend == "avro":
            from .avro import AvroSerializer
            return AvroSerializer()
        raise NotImplementedError()
