import asyncio
from abc import ABC, abstractmethod


class RpcClient(ABC):
    @abstractmethod
    async def connect(self, server_host: str, server_port: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError()


def create_rpc_client(
    name: str,
    codec_name: str,
    incoming: asyncio.Queue,
    outgoing: asyncio.Queue,
) -> RpcClient:
    assert name == "websocket"
    from .websocket import WebsocketRPC

    return WebsocketRPC(
        codec_name=codec_name,
        incoming=incoming,
        outgoing=outgoing,
    )
