import asyncio
import http
import logging
from typing import Optional, Tuple

from websockets.datastructures import Headers, HeadersLike
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve

from . import RpcServer


class WebsocketRPC(RpcServer):
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
        self.active = False
        self.send_source = send_source
        self.recv_sink = recv_sink
        self.logger = logging.getLogger(__name__)

    async def __handle_outgoing__(
        self,
        websocket: WebSocketServerProtocol,
    ):
        """
        Write message from queue into the websocket

        Args:
            websocket (WebSocketServerProtocol): websocket connection

        """
        while self.active and websocket.open:
            message = await self.send_source.get()
            self.logger.debug(f"outgoing message: {message}")
            if isinstance(message, bytes):
                await websocket.send(message)
            if isinstance(message, list):
                for frame in message:
                    await websocket.send(frame)

    async def __handle_incoming__(
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
            self.logger.debug(f"incoming message: {message}")
            await self.recv_sink.put(message)

    async def __handle__(
        self,
        websocket: WebSocketServerProtocol,
    ):
        self.logger.info(f"client connected: {websocket.remote_address}")
        task1 = asyncio.create_task(self.__handle_outgoing__(websocket))
        task2 = asyncio.create_task(self.__handle_incoming__(websocket))
        done, pending = await asyncio.wait([task1, task2])
        for task in pending:
            task.cancel()
        self.logger.info(f"client disconnected: {websocket.remote_address}")

    async def __intercept__(
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
            ws_handler=self.__handle__,
            host=host,
            port=port,
            process_request=self.__intercept__,
        )

    async def stop(
        self,
    ):
        self.active = False
        self.server.close()
