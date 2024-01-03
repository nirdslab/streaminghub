from .codec import Codec


def create_codec(
    backend: str,
) -> Codec:
    if backend == "json":
        from .json import JSONCodec

        return JSONCodec()
    if backend == "avro":
        from .avro import AvroCodec

        return AvroCodec()
    raise NotImplementedError()
