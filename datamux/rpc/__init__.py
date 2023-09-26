import asyncio


class RpcServer:
    async def start(self, host: str, port: int) -> None:
        raise NotImplementedError()
    
    async def stop(self) -> None:
        raise NotImplementedError()


class RpcClient:
    async def connect(self, server_host: str, server_port: int) -> None:
        raise NotImplementedError()

    async def disconnect(self) -> None:
        raise NotImplementedError()


def create_rpc_server(
    name: str,
    send_source: asyncio.Queue,
    recv_sink: asyncio.Queue,
) -> RpcServer:
    assert name == "websocket"
    from .websocket import WebsocketRpcServer

    return WebsocketRpcServer(send_source, recv_sink)


def create_rpc_client(
    name: str,
    send_source: asyncio.Queue,
    recv_sink: asyncio.Queue,
) -> RpcClient:
    assert name == "websocket"
    from .websocket import WebsocketRpcClient

    return WebsocketRpcClient(send_source, recv_sink)
