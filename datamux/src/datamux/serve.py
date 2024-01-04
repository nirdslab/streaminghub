#!/usr/bin/env python3

import asyncio
import logging

from rich.logging import RichHandler

from datamux.remote.server import DataMuxServer


async def serve(
    host: str,
    port: int,
    rpc: str,
    codec: str,
):
    server = DataMuxServer(rpc_name=rpc, codec_name=codec)
    await server.start(host, port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)

    host = "localhost"
    port = 3300
    rpc = "websocket"
    codec = "avro"
    try:
        asyncio.run(serve(host, port, rpc, codec))
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
