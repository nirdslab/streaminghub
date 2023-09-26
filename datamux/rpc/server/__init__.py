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
    send_source: asyncio.Queue,
    recv_sink: asyncio.Queue,
) -> RpcServer:
    assert name == "websocket"
    from .websocket import WebsocketRPC

    return WebsocketRPC(send_source, recv_sink)
