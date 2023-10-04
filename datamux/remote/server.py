import asyncio

from api import DataMuxAPI
from rpc import create_rpc_server

from .topics import *


class DataMuxServer:
    """
    Serves the DataMux API for Remote Use

    """

    def __init__(
        self,
        rpc_name: str,
        codec_name: str,
    ) -> None:
        self.active = False
        self.api_in = asyncio.Queue()
        self.api_out = asyncio.Queue()
        # rpc module
        self.rpc = create_rpc_server(
            name=rpc_name,
            codec_name=codec_name,
            incoming=self.api_in,
            outgoing=self.api_out,
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
            topic, content, id = await self.api_in.get()

            transform = lambda retval: [topic, retval, id]

            # LIVE MODE (LSL -> Queue) =================================================================================================
            if topic == TOPIC_LIST_LIVE_STREAMS:
                streams = self.api.list_live_streams()
                retval = [s.model_dump() for s in streams]
            elif topic == TOPIC_READ_LIVE_STREAM:
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                ack = self.api.read_live_stream(stream_name, attrs, self.api_out, transform)
                retval = ack.model_dump()
            # REPLAY MODE (File -> Queue) ==============================================================================================
            elif topic == TOPIC_LIST_COLLECTIONS:
                collections = self.api.list_collections()
                retval = [c.model_dump() for c in collections]
            elif topic == TOPIC_LIST_COLLECTION_STREAMS:
                collec_name = content["collection_name"]
                streams = self.api.list_collection_streams(collec_name)
                retval = [s.model_dump() for s in streams]
            elif topic == TOPIC_REPLAY_COLLECTION_STREAM:
                collec_name = content["collection_name"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                ack = self.api.replay_collection_stream(collec_name, stream_name, attrs, self.api_out, transform)
                retval = ack.model_dump()
            # RESTREAM MODE (File -> LSL) ==============================================================================================
            elif topic == TOPIC_PUBLISH_COLLECTION_STREAM:
                collection_name = content["collection_name"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                ack = self.api.publish_collection_stream(collection_name, stream_name, attrs)
                retval = ack.model_dump()
            # FALLBACK =================================================================================================================
            else:
                retval = dict(error="Unknown Request")

            msg = transform(retval)
            await self.api_out.put(msg)

    async def start(
        self,
        host: str,
        port: int,
    ):
        self.active = True
        asyncio.create_task(self.handle_requests())
        asyncio.create_task(self.rpc.start(host, port))
        flag = asyncio.Future()
        await flag

    async def stop(
        self,
    ):
        self.active = False
        await self.rpc.stop()
