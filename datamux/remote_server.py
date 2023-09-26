import asyncio

from api import DataMuxAPI
from codec import create_codec
from rpc import create_rpc_server
from remote_topics import *


class DataMuxServer:
    """
    Serves the DataMux API for Remote Use

    """

    def __init__(
        self,
        rpc_backend: str,
        serialization_backend: str,
    ) -> None:
        self.active = False
        # queues - sending
        self.codec_send_source = self.api_send_sink = asyncio.Queue()
        self.rpc_send_source = self.codec_send_sink = asyncio.Queue()
        # queues - receiving
        self.codec_recv_source = self.rpc_recv_sink = asyncio.Queue()
        self.api_recv_source = self.codec_recv_sink = asyncio.Queue()
        # rpc module
        self.rpc = create_rpc_server(
            name=rpc_backend,
            send_source=self.rpc_send_source,
            recv_sink=self.rpc_recv_sink,
        )
        # codec module
        self.codec = create_codec(
            backend=serialization_backend,
            send_source=self.codec_send_source,
            send_sink=self.codec_send_sink,
            recv_source=self.codec_recv_source,
            recv_sink=self.codec_recv_sink,
        )
        # api module
        self.api = DataMuxAPI()

    async def handle_requests(
        self,
    ):
        """
        Handle Requests sent to DataMuxServer

        Args:
            topic (bytes): topic of the message
            content (dict): content of the message
        """

        while self.active:
            topic, content = await self.api_recv_source.get()
            # LIVE MODE (LSL -> Queue) =================================================================================================
            if topic == TOPIC_LIST_LIVE_STREAMS:
                retval = self.api.list_live_streams()
            elif topic == TOPIC_RELAY_LIVE_STREAM:
                retval = self.api.relay_live_streams(
                    content["stream_name"],
                    content["attrs"],
                    self.api_send_sink,
                )
            # REPLAY MODE (File -> Queue) ==============================================================================================
            elif topic == TOPIC_LIST_COLLECTIONS:
                retval = self.api.list_collections()
            elif topic == TOPIC_LIST_COLLECTION_STREAMS:
                retval = self.api.list_collection_streams(
                    content["collection_name"],
                )
            elif topic == TOPIC_REPLAY_COLLECTION_STREAM:
                retval = self.api.replay_collection_stream(
                    content["collection_name"],
                    content["stream_name"],
                    content["attrs"],
                    self.api_send_sink,
                )
            # RESTREAM MODE (File -> LSL) ==============================================================================================
            elif topic == TOPIC_RESTREAM_COLLECTION_STREAM:
                collection_name = content["collection_name"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                retval = self.api.restream_collection_stream(
                    collection_name,
                    stream_name,
                    attrs,
                )
            # FALLBACK =================================================================================================================
            else:
                retval = dict(error="Unknown Request")

            await self.api_send_sink.put((topic, retval))

    async def start(
        self,
        host: str,
        port: int,
    ):
        self.active = True
        self.codec.start()
        asyncio.create_task(self.handle_requests())
        asyncio.create_task(self.rpc.start(host, port))
        flag = asyncio.Future()
        await flag

    async def stop(
        self,
    ):
        self.active = False
        await self.rpc.stop()
        self.codec.stop()
