import asyncio
from logging import getLogger
from typing import Tuple


class Codec:
    """
    Base Class for Serialization / Deserialization

    """

    def __init__(
        self,
        send_source: asyncio.Queue,
        send_sink: asyncio.Queue,
        recv_source: asyncio.Queue,
        recv_sink: asyncio.Queue,
    ):
        self.send_source = send_source
        self.send_sink = send_sink
        self.recv_source = recv_source
        self.recv_sink = recv_sink
        self.logger = getLogger(__name__)
        self.active = False

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

    async def send_loop(
        self,
        source: asyncio.Queue,
        sink: asyncio.Queue,
    ):
        while not self.active:
            topic, content = await source.get()
            self.logger.warn(topic)
            message = self.encode(topic, content)
            await sink.put(message)

    async def recv_loop(
        self,
        source: asyncio.Queue,
        sink: asyncio.Queue,
    ):
        while not self.active:
            message = await source.get()
            decoded_message = self.decode(message)
            if decoded_message:
                topic, content = decoded_message
                self.logger.warn(topic)
                await sink.put((topic, content))

    def start(
        self,
    ):
        self.active = True
        asyncio.create_task(self.send_loop(self.send_source, self.send_sink))
        asyncio.create_task(self.recv_loop(self.recv_source, self.recv_sink))

    def stop(
        self,
    ):
        self.active = False

    @staticmethod
    def with_backend(
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
