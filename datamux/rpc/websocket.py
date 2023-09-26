import asyncio
import http
import logging
from typing import Optional, Tuple

from websockets.client import WebSocketClientProtocol, connect
from websockets.datastructures import Headers, HeadersLike
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve

from . import RpcClient, RpcServer


class WebsocketRpcServer(RpcServer):
    """
    WebSocket RPC server

    """

    def __init__(
        self,
        send_source: asyncio.Queue,
        recv_sink: asyncio.Queue,
    ) -> None:
        """
        Args:
            serializer (Serializer) serializer to encode/decode outgoing/incoming messages
            send_source (asyncio.Queue) outgoing message queue
            recv_sink (asyncio.Queue) incoming message queue
        """
        self.send_source = send_source
        self.recv_sink = recv_sink
        self.logger = logging.getLogger(__name__)

    async def send_loop(
        self,
        websocket: WebSocketServerProtocol,
    ):
        """
        Write content from queue into the websocket

        Args:
            websocket (WebSocketServerProtocol): websocket connection

        """
        while self.active and websocket.open:
            content = await self.send_source.get()
            if isinstance(content, bytes):
                await websocket.send(content)
            if isinstance(content, list):
                for msg in content:
                    await websocket.send(msg)

    async def recv_loop(
        self,
        websocket: WebSocketServerProtocol,
    ):
        """
        Read content from websocket into the queue

        Args:
            websocket (WebSocketServerProtocol): websocket connection

        """

        while self.active and websocket.open:
            try:
                message = await websocket.recv()
            except ConnectionClosed:
                self.logger.info(f"client connection closed: {websocket.remote_address}")
                break
            assert isinstance(message, bytes)
            await self.recv_sink.put(message)

    async def handler(
        self,
        websocket: WebSocketServerProtocol,
    ):
        self.logger.info(f"client connected: {websocket.remote_address}")
        send_task = asyncio.create_task(self.send_loop(websocket))
        recv_task = asyncio.create_task(self.recv_loop(websocket))
        done, pending = await asyncio.wait([send_task, recv_task])
        for task in pending:
            task.cancel()
        self.logger.info(f"client disconnected: {websocket.remote_address}")

    async def middleware(
        self,
        path: str,
        headers: Headers,
    ) -> Optional[Tuple[http.HTTPStatus, HeadersLike, bytes]]:
        if path == "/ws":
            return None
        elif path == "/":
            return http.HTTPStatus(200), [], b""
        else:
            return http.HTTPStatus(404), [], b""

    async def start(
        self,
        host: str,
        port: int,
    ):
        self.active = True
        self.server = await serve(
            ws_handler=self.handler,
            host=host,
            port=port,
            process_request=self.middleware,
        )

    async def stop(
        self,
    ):
        self.active = False
        self.server.close()


class WebsocketRpcClient(RpcClient):
    """
    WebSocket RPC Client

    """

    def __init__(
        self,
        send_source: asyncio.Queue,
        recv_sink: asyncio.Queue,
    ) -> None:
        self.send_source = send_source
        self.recv_sink = recv_sink
        self.logger = logging.getLogger(__name__)

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ) -> None:
        uri = f"ws://{server_host}:{server_port}/ws"
        self.websocket = await connect(uri)
        self.logger.info(f"Connected to WebSocket Server: {uri}")
        assert self.websocket is not None
        asyncio.create_task(self.send_loop(self.websocket))
        asyncio.create_task(self.recv_loop(self.websocket))

    async def disconnect(
        self,
    ):
        await asyncio.create_task(self.websocket.close())

    async def send_loop(
        self,
        websocket: WebSocketClientProtocol,
    ):
        while websocket.open:
            message = await self.send_source.get()
            if isinstance(message, bytes):
                await self.websocket.send(message)
            else:
                for msg in message:
                    await self.websocket.send(msg)

    async def recv_loop(
        self,
        websocket: WebSocketClientProtocol,
    ):
        while websocket.open:
            recvmsg = await self.websocket.recv()
            await self.recv_sink.put(recvmsg)
