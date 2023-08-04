#!/usr/bin/env python3
import asyncio
import random
import time
import unittest

import pylsl

from mock.empatica_e4ss import Connector


async def listen(inlet: pylsl.StreamInlet):
  while True:
    samples, timestamps = inlet.pull_chunk()
    for sample, timestamp in zip(samples, timestamps):
      print('\t'.join(map(lambda x: str(x).ljust(20), [inlet.info().type(), timestamp, sample])), flush=True)
    await asyncio.sleep(0.1)


async def emit(conn: Connector, name: str, freq: int, channels: int):
  while True:
    t = round(time.time_ns() * 1e-9, 2)
    cmd = f"{name} {str(t)}"
    if channels > 0:
      cmd = f"{cmd} {' '.join(map(lambda x: str(random.gauss(0, 0.25)), range(channels)))}"
    conn.process_data_stream(cmd)
    await asyncio.sleep(1. / freq)


class TestEmpaticaE4(unittest.TestCase):

  def setUp(self) -> None:
    super().setUp()

  def test_inlet(self):
    print("looking for an Empatica E4 stream...")
    streams = pylsl.resolve_stream('name', 'E4, Empatica (Wristband)')
    assert len(streams) > 0
    print(f'{len(streams)} Stream(s) found!')

    # create a new inlets to read from the streams
    jobs = [listen(pylsl.StreamInlet(stream)) for stream in streams]

    try:
      print('started listeners')
      asyncio.get_event_loop().run_until_complete(asyncio.gather(*jobs))
    except KeyboardInterrupt:
      print('stopped listeners')

  def test_outlet(self):
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
    conn = Connector()
    jobs = [emit(conn, *arg) for arg in args]
    conn.device_id = '1234567890'
    try:
      print('started streaming')
      asyncio.get_event_loop().run_until_complete(asyncio.gather(*jobs))
    except KeyboardInterrupt:
      print('stopped streaming')

  def tearDown(self) -> None:
    super().tearDown()
