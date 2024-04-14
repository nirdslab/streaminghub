import asyncio
from abc import ABC, abstractmethod


class RpcClient(ABC):
    """
    Base Class for RPC Client

    """

    @abstractmethod
    def __init__(
        self,
        codec_name: str,
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None: ...

    @abstractmethod
    async def connect(self, server_host: str, server_port: int) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...
