import asyncio
import logging

from websockets.client import WebSocketClientProtocol, connect

from . import RpcClient


class WebsocketRPC(RpcClient):
    """
    WebSocket RPC Client

    """

    def __init__(
        self,
        send_source: asyncio.Queue,
        recv_sink: asyncio.Queue,
    ) -> None:
        self.active = False
        self.send_source = send_source
        self.recv_sink = recv_sink
        self.logger = logging.getLogger(__name__)

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ) -> None:
        self.active = True
        uri = f"ws://{server_host}:{server_port}/ws"
        self.websocket = await connect(uri)
        self.logger.info(f"Connected to WebSocket Server: {uri}")
        assert self.websocket is not None
        asyncio.create_task(self.__handle_outgoing__(self.websocket))
        asyncio.create_task(self.__handle_incoming__(self.websocket))

    async def disconnect(
        self,
    ):
        self.active = False
        await asyncio.create_task(self.websocket.close())

    async def __handle_outgoing__(
        self,
        websocket: WebSocketClientProtocol,
    ):
        while self.active and websocket.open:
            message: bytes | list[bytes] = await self.send_source.get()
            self.logger.debug(f"outgoing message: {message}")
            if isinstance(message, bytes):
                await self.websocket.send(message)
            else:
                for msg in message:
                    await self.websocket.send(msg)

    async def __handle_incoming__(
        self,
        websocket: WebSocketClientProtocol,
    ):
        while self.active and websocket.open:
            message = await self.websocket.recv()
            self.logger.debug(f"incoming message: {message}")
            await self.recv_sink.put(message)
