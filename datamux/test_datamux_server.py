#!/usr/bin/env python3

import asyncio
import logging

from dotenv import load_dotenv

from datamux import DataMuxServer


async def main():
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)

    load_dotenv()

    host = "localhost"
    port = 3300
    datamux = DataMuxServer(rpc_backend="websocket", serialization_backend="avro")
    await datamux.start(host, port)


if __name__ == "__main__":
    asyncio.run(main())
