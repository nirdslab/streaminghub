#!/usr/bin/env python3

import asyncio
import logging

from rich.logging import RichHandler

from datamux.remote.server import DataMuxServer


async def serve(host: str, port: int):
    server = DataMuxServer(rpc_name="websocket", codec_name="json")
    await server.start(host, port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)

    host = "localhost"
    port = 3300
    try:
        asyncio.run(serve(host, port))
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
