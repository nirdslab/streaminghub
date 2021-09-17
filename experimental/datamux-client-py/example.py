import asyncio
import logging
from pprint import pprint

from datamux.client import DataMuxClient


async def main():
  client = DataMuxClient("ws://localhost:8765/ws")
  await client.connect()
  live_streams = await client.get_live_streams()
  pprint(live_streams)
  datasets = await client.get_datasets()
  pprint(datasets)
  await client.disconnect()


if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.DEBUG)
  asyncio.run(main())
