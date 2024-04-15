import asyncio
from abc import ABC, abstractmethod

from streaminghub_datamux.rpc.codec import RpcCodec


class RpcServer(ABC):
    """
    Base Class for RPC Server

    """

    @abstractmethod
    def __init__(
        self,
        codecs: dict[str, type[RpcCodec]],
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None: ...

    @abstractmethod
    async def start(self, host: str, port: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
