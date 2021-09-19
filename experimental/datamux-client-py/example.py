import asyncio
import logging
from pprint import pprint

from datamux.client import DataMuxClient

logger = logging.getLogger()


async def main():
  # establish connection
  client = DataMuxClient("ws://localhost:8765/ws")
  await client.connect()
  # get live streams
  live_streams = await client.get_live_streams()
  if len(live_streams) > 0:
    pprint(live_streams[0])
  # get datasets
  await client.get_datasets()
  # subscribe to a dataset
  dataset_name = 'n_back'
  repl_streams = await client.get_repl_streams(dataset_name)
  # subscribe to first repl stream in dataset
  if len(repl_streams) > 0:
    pprint(repl_streams[0])
  await client.disconnect()


if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)-15s %(message)s', level=logging.INFO)
  asyncio.run(main())
