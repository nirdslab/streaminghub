import asyncio


def create_codec(
    backend: str,
    send_source: asyncio.Queue,
    send_sink: asyncio.Queue,
    recv_source: asyncio.Queue,
    recv_sink: asyncio.Queue,
):
    if backend == "json":
        from .json import JSONCodec

        return JSONCodec(send_source, send_sink, recv_source, recv_sink)
    if backend == "avro":
        from .avro import AvroCodec

        return AvroCodec(send_source, send_sink, recv_source, recv_sink)
    raise NotImplementedError()
