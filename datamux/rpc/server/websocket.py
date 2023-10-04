import asyncio
import http
import logging
from collections import defaultdict
from typing import Optional, Tuple

from websockets.datastructures import Headers, HeadersLike
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve

from codec import Codec, create_codec

from . import RpcServer


class WebsocketRPC(RpcServer):
    """
    WebSocket RPC server

    """

    def __init__(
        self,
        codec_name: str,
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None:
        """
        Args:
            codec_name (str) codec to encode/decode outgoing/incoming messages
            incoming (asyncio.Queue) incoming messages from ALL clients
            outgoing (asyncio.Queue) outgoing messages for ALL clients
        """
        self.active = False
        # multiplexed queue
        self.incoming = incoming
        self.outgoing = outgoing
        # demultiplexed queues
        self.demux: dict[bytes, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())
        # codec module
        self.codec_name = codec_name
        self.logger = logging.getLogger(__name__)

    async def __handle_demux__(self):
        """
        Demultiplex global outgoing to specific sources

        """
        self.logger.info("started demultiplexer")
        while self.active:
            (topic, content, id) = await self.outgoing.get()
            try:
                await self.demux[id].put((topic, content))
            except:
                self.logger.error(f"error in outgoing for id={id}")

    async def __handle_outgoing__(
        self,
        websocket: WebSocketServerProtocol,
        codec: Codec,
    ):
        """
        Write message from queue into the websocket

        Args:
            websocket (WebSocketServerProtocol): websocket connection

        """
        id = websocket.id.bytes
        try:
            while self.active:
                (topic, content) = await self.demux[id].get()
                self.logger.debug(f">: {topic}: {content}")
                msg = codec.encode(topic, content)
                if isinstance(msg, bytes):
                    await websocket.send(msg)
                if isinstance(msg, list):
                    for frame in msg:
                        await websocket.send(frame)
        except ConnectionClosed:
            self.logger.info(f"client connection closed: {id}")

    async def __handle_incoming__(
        self,
        websocket: WebSocketServerProtocol,
        codec: Codec,
    ):
        """
        Read content from websocket into the queue

        Args:
            websocket (WebSocketServerProtocol): websocket connection

        """
        id = websocket.id.bytes
        try:
            while self.active:
                msg = await websocket.recv()
                assert isinstance(msg, bytes)
                if (msg := codec.decode(msg)) is not None:
                    topic, content = msg
                    self.logger.debug(f"<: {topic}: {content}")
                    await self.incoming.put((topic, content, id))
        except ConnectionClosed:
            self.logger.info(f"client connection closed: {id}")

    async def __handle__(
        self,
        websocket: WebSocketServerProtocol,
    ):
        id = websocket.id.bytes
        codec = create_codec(self.codec_name)
        self.logger.info(f"client connected: {websocket.id}")
        outgoing = asyncio.create_task(self.__handle_outgoing__(websocket, codec))
        incoming = asyncio.create_task(self.__handle_incoming__(websocket, codec))
        done, pending = await asyncio.wait([outgoing, incoming], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        self.logger.info(f"client disconnected: {id}")

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
        asyncio.create_task(self.__handle_demux__())

    async def stop(
        self,
    ):
        self.active = False
        self.server.close()
