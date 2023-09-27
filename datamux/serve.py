#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from remote.server import DataMuxServer


async def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()

    host = "localhost"
    port = 3300
    server = DataMuxServer(rpc_backend="websocket", serialization_backend="avro")
    await server.start(host, port)


if __name__ == "__main__":
    asyncio.run(main())
