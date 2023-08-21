import asyncio
import http
import logging
from typing import Optional, Tuple

from websockets.datastructures import Headers, HeadersLike
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve
from websockets.client import connect

from datamux import DataMuxClient, DataMuxProtocol, DataMuxServer
from serializers import Serializer


class WebsocketServer:
    """
    A simple WebSocket server for DataMux.

    """

    def __init__(
        self,
        host: str,
        port: int,
        backend: str = "json",
    ) -> None:
        self.host = host
        self.port = port
        self.serializer = Serializer.for_backend(backend)
        self.logger = logging.getLogger()
        self.protocol = DataMuxProtocol()
        self.datamux = DataMuxServer(self.protocol)

    async def producer_handler(
        self,
        websocket: WebSocketServerProtocol,
        **kwargs,
    ):
        """
        Write content from queue into the websocket

        Args:
            websocket (WebSocketServerProtocol): websocket connection
        """
        while websocket.open:
            topic, content = await self.datamux.deque()
            self.logger.debug(f"<: {topic}, {content}")
            message = self.serializer.encode(topic, content)
            if isinstance(message, bytes):
                await websocket.send(message)
            else:
                for msg in message:
                    await websocket.send(msg)

    async def consumer_handler(
        self,
        websocket: WebSocketServerProtocol,
        **kwargs,
    ):
        while websocket.open:
            try:
                message = await websocket.recv()
            except ConnectionClosed:
                self.logger.info(f"client connection closed: {websocket.remote_address}")
                break
            assert isinstance(message, bytes)
            topic, content = self.serializer.decode(message)
            self.logger.debug(f"<: {topic}, {content}")
            if topic.startswith(b"schema_"):
                self.serializer.bind_schema(topic[7:], content)
            else:
                await self.datamux.process(topic, **content)

    async def ws_handler(
        self,
        websocket: WebSocketServerProtocol,
        **kwargs,
    ):
        self.logger.info(f"client connected: {websocket.remote_address}")
        producer_task = asyncio.create_task(self.producer_handler(websocket, **kwargs))
        consumer_task = asyncio.create_task(self.consumer_handler(websocket, **kwargs))
        done, pending = await asyncio.wait([producer_task, consumer_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        self.logger.info(f"client disconnected: {websocket.remote_address}")

    async def process_request(
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

    async def serve(
        self,
    ):
        stop = asyncio.Future()
        async with serve(
            ws_handler=self.ws_handler,
            host=self.host,
            port=self.port,
            process_request=self.process_request,
        ):
            await stop


class WebsocketClient:
    """
    A simple WebSocket client for DataMux.

    """

    def __init__(
        self,
        server_host: str,
        server_port: int,
        backend: str = "json",
    ) -> None:
        self.host = server_host
        self.port = server_port
        self.serializer = Serializer.for_backend(backend)
        self.logger = logging.getLogger()
        self.protocol = DataMuxProtocol()
        self.datamux = DataMuxClient(self.protocol)

    async def connect(
        self,
    ):
        uri = f"ws://{self.host}:{self.port}/ws"
        self.websocket = await connect(uri)
        self.logger.info(f"Connected to DataMux: {uri}")

    async def sendmsg(
        self,
        topic: bytes,
        content: dict,
    ):
        sendmsg = self.serializer.encode(topic, content)
        await self.websocket.send(sendmsg)

    async def recvmsg(
        self,
    ):
        recvmsg: bytes = await self.websocket.recv()  # type: ignore
        topic, content = self.serializer.decode(recvmsg)
        self.logger.info(f"topic: {topic}")
        self.logger.info(f"content: {content}")
        if topic.startswith(b"schema_"):
            self.serializer.bind_schema(topic[7:], content)
        return topic, content
