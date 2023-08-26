#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from serving import WebsocketServer


async def main():
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)

    load_dotenv()

    host = "localhost"
    port = 3300
    datamux = WebsocketServer(host, port, backend="avro")
    await datamux.serve()


if __name__ == "__main__":
    asyncio.run(main())
