import asyncio
import logging

from streaminghub_datamux.rpc import RpcClient, RpcCodec, create_rpc_codec
from websockets.client import WebSocketClientProtocol, connect


class WebsocketClient(RpcClient):
    """
    WebSocket RPC Client

    """

    def __init__(
        self,
        codec_name: str,
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None:
        self.active = False
        self.codec_name = codec_name
        self.incoming = incoming
        self.outgoing = outgoing
        self.logger = logging.getLogger(__name__)

    async def connect(
        self,
        server_host: str,
        server_port: int,
    ) -> None:
        self.active = True
        uri = f"ws://{server_host}:{server_port}/ws"
        self.websocket = await connect(uri, extra_headers={"X-CODEC": self.codec_name})
        self.logger.info(f"Connected to WebSocket Server: {uri}")
        assert self.websocket is not None
        codec = create_rpc_codec(self.codec_name)
        asyncio.create_task(self.__handle_outgoing__(self.websocket, codec))
        asyncio.create_task(self.__handle_incoming__(self.websocket, codec))

    async def disconnect(
        self,
    ):
        self.active = False
        await asyncio.create_task(self.websocket.close())

    async def __handle_outgoing__(
        self,
        websocket: WebSocketClientProtocol,
        codec: RpcCodec,
    ):
        while self.active and websocket.open:
            topic, content = await self.outgoing.get()
            self.logger.debug(f">: {topic}: {content}")
            msg: bytes | list[bytes] = codec.encode(topic, content)
            if isinstance(msg, bytes):
                await self.websocket.send(msg)
            if isinstance(msg, list):
                for frame in msg:
                    await self.websocket.send(frame)

    async def __handle_incoming__(
        self,
        websocket: WebSocketClientProtocol,
        codec: RpcCodec,
    ):
        while self.active and websocket.open:
            msg = await self.websocket.recv()
            assert isinstance(msg, bytes)
            if (val := codec.decode(msg)) is not None:
                topic, content = val
                self.logger.debug(f"<: {topic}: {content}")
                await self.incoming.put((topic, content))
