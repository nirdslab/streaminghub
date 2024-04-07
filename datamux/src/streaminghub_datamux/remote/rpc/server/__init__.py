import asyncio
from abc import ABC, abstractmethod


class RpcServer(ABC):
    @abstractmethod
    async def start(self, host: str, port: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError()


def create_rpc_server(
    name: str,
    codec_name: str,
    incoming: asyncio.Queue,
    outgoing: asyncio.Queue,
) -> RpcServer:
    assert name == "websocket"
    from .websocket import WebsocketRPC

    return WebsocketRPC(
        codec_name=codec_name,
        incoming=incoming,
        outgoing=outgoing,
    )
