#!/usr/bin/env python3
import asyncio
import random
import time

from devices.empatica_e4.connector import Connector


async def emit(conn: Connector, name: str, freq: int, channels: int):
  while True:
    t = round(time.time_ns() * 1e-9, 2)
    cmd = f"{name} {str(t)}"
    if channels > 0:
      cmd = f"{cmd} {' '.join(map(lambda x: str(random.gauss(0, 0.25)), range(channels)))}"
    conn.process_data_stream(cmd)
    await asyncio.sleep(1. / freq)


async def main():
  args = [
    ('E4_Acc', 2, 3),
    ('E4_Bvp', 4, 1),
    ('E4_Gsr', 1, 1),
    ('E4_Ibi', 1, 1),
    ('E4_Temperature', 1, 1),
    ('E4_Battery', 0.5, 1),
    ('E4_Tag', 0.25, 0)
  ]
  print(f'{len(args)} streams created')
  print(f'streaming started')
  conn = Connector()
  jobs = [emit(conn, *arg) for arg in args]
  conn.device_id = '1234567890'
  await asyncio.gather(*jobs)


if __name__ == '__main__':
  try:
    print('starting streaming...')
    asyncio.get_event_loop().run_until_complete(main())
  except KeyboardInterrupt:
    print('streaming stopped')
