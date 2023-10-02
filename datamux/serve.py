#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv
from rich.logging import RichHandler

from remote.server import DataMuxServer


async def main():

    load_dotenv()

    host = "localhost"
    port = 3300
    server = DataMuxServer(rpc_backend="websocket", serialization_backend="avro")
    await server.start(host, port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    logger = logging.getLogger(__name__)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
