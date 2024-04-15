import asyncio
import multiprocessing
from threading import Thread

from streaminghub_datamux.api import DataMuxAPI
from streaminghub_datamux.rpc import create_rpc_server

from .topics import *


class DataMuxServer:
    """
    Serves the DataMux API for Remote Use

    """

    def __init__(
        self,
        rpc_name: str,
    ) -> None:
        self.active = False
        self.api_in = asyncio.Queue()
        self.api_out = asyncio.Queue()
        self.data_q = multiprocessing.Queue()
        # rpc module
        self.rpc = create_rpc_server(
            name=rpc_name,
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
            transform = lambda retval: [retval, id]

            # LIVE MODE (LSL -> Queue) =================================================================================================
            if topic == TOPIC_LIST_LIVE_STREAMS:
                node_id = content["node_id"]
                streams = self.api.list_live_streams(node_id)
                retval = [s.model_dump() for s in streams]
            elif topic == TOPIC_READ_LIVE_STREAM:
                node_id = content["node_id"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                ack = self.api.proxy_live_stream(node_id, stream_name, attrs, self.data_q, transform)
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
                ack = self.api.replay_collection_stream(collec_name, stream_name, attrs, self.data_q, transform)
                retval = ack.model_dump()
            # RESTREAM MODE (File -> LSL) ==============================================================================================
            elif topic == TOPIC_PUBLISH_COLLECTION_STREAM:
                collection_name = content["collection_name"]
                stream_name = content["stream_name"]
                attrs = content["attrs"]
                ack = self.api.publish_collection_stream(collection_name, stream_name, attrs)
                retval = ack.model_dump()
            # ACTIONS ==================================================================================================================
            elif topic == TOPIC_STOP_TASK:
                randseq = content["randseq"]
                ack = self.api.stop_task(randseq)
                retval = ack.model_dump()
            # FALLBACK =================================================================================================================
            else:
                retval = dict(error="Unknown Request")

            msg = [topic] + transform(retval)
            self.api_out.put_nowait(msg)

    def requeue(
        self,
        loop: asyncio.AbstractEventLoop,
    ):
        while self.active:
            msg = self.data_q.get()
            loop.call_soon_threadsafe(self.api_out.put_nowait, msg)

    async def start(
        self,
        host: str,
        port: int,
    ):
        self.active = True
        loop = asyncio.get_running_loop()
        Thread(None, self.requeue, None, (loop,), daemon=True).start()
        asyncio.create_task(self.handle_requests())
        asyncio.create_task(self.rpc.start(host, port))
        flag = asyncio.Future()
        await flag

    async def stop(
        self,
    ):
        self.active = False
        await self.rpc.stop()
