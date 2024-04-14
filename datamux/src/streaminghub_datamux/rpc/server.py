import asyncio
from abc import ABC, abstractmethod


class RpcServer(ABC):
    """
    Base Class for RPC Server

    """

    @abstractmethod
    def __init__(
        self,
        codec_name: str,
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None: ...

    @abstractmethod
    async def start(self, host: str, port: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
