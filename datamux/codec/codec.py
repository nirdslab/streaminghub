import asyncio
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Tuple


class Codec(ABC):
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

    @abstractmethod
    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes | list[bytes]:
        raise NotImplementedError()

    @abstractmethod
    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict] | None:
        raise NotImplementedError()

    async def __handle_outgoing__(
        self,
    ):
        while self.active:
            topic, content = await self.send_source.get()
            self.logger.warn(topic)
            message = self.encode(topic, content)
            await self.send_sink.put(message)

    async def __handle_incoming__(
        self,
    ):
        while self.active:
            message = await self.recv_source.get()
            decoded_message = self.decode(message)
            if decoded_message:
                topic, content = decoded_message
                self.logger.warn(topic)
                await self.recv_sink.put((topic, content))

    def start(
        self,
    ):
        self.active = True
        asyncio.create_task(self.__handle_outgoing__())
        asyncio.create_task(self.__handle_incoming__())

    def stop(
        self,
    ):
        self.active = False
