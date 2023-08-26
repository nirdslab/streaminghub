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
        self.serializer = Serializer.with_backend(backend)
        self.logger = logging.getLogger(__name__)
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
            self.logger.debug(f"sending: {topic}, {content}")
            message = self.serializer.encode(topic, content)
            if isinstance(message, bytes):
                self.logger.debug(f"encoded: {message}")
                await websocket.send(message)
            else:
                for msg in message:
                    self.logger.debug(f"encoded: {msg}")
                    await websocket.send(msg)

    async def consumer_handler(
        self,
        websocket: WebSocketServerProtocol,
        **kwargs,
    ):
        while websocket.open:
            try:
                message = await websocket.recv()
                self.logger.debug(f"received: {message}")
            except ConnectionClosed:
                self.logger.info(f"client connection closed: {websocket.remote_address}")
                break
            assert isinstance(message, bytes)
            readout = self.serializer.decode(message)
            if readout is not None:
                topic, content = readout
                self.logger.debug(f"decoded: {topic}, {content}")
                await self.datamux.process(topic, **content)
            else:
                self.logger.warn(f"got empty message: {message}")

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
        self.serializer = Serializer.with_backend(backend)
        self.logger = logging.getLogger(__name__)
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
        self.logger.debug(f"sending: {topic}, {content}")
        sendmsg = self.serializer.encode(topic, content)
        if isinstance(sendmsg, bytes):
            self.logger.debug(f"encoded: {sendmsg}")
            await self.websocket.send(sendmsg)
        else:
            for msg in sendmsg:
                self.logger.debug(f"encoded: {msg}")
                await self.websocket.send(msg)

    async def recvmsg(
        self,
    ):
        try:
            recvmsg: bytes = await self.websocket.recv()  # type: ignore
            self.logger.debug(f"received: {recvmsg}")
            readout = self.serializer.decode(recvmsg)
            if readout is not None:
                topic, content = readout
                self.logger.debug(f"decoded: {topic}, {content}")
                return topic, content
            else:
                self.logger.warn(f"got empty message: {recvmsg}")
                return None
        except Exception as e:
            self.logger.error(f"error in recvmsg(): {e}")
            return None
