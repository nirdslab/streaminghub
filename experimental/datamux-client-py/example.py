import asyncio
import logging

from datamux.client import DataMuxClient

logger = logging.getLogger()


async def main():
  client = DataMuxClient("ws://localhost:8765/ws")
  await client.connect()
  await client.get_live_streams()
  await client.get_datasets()
  dataset_name = 'n_back'
  await client.get_repl_streams(dataset_name)
  await client.disconnect()


if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
  asyncio.run(main())
