#!/usr/bin/env python3
import asyncio
import time
from random import randint

import empatica_e4.connector as conn


async def emit(name, freq, channels):
    while True:
        conn.process_data_stream(f"{name} {' '.join(map(str, [round(time.time_ns() * 1e-9, 2), *[randint(1, 5) for _ in range(channels)]]))}")
        await asyncio.sleep(1 / freq)


async def main():
    args = [
        ('E4_Acc', 32, 3),
        ('E4_Bvp', 64, 1),
        ('E4_Gsr', 1, 1),
        ('E4_Ibi', 1, 1),
        ('E4_Hr', 1, 1),
        ('E4_Temperature', 0.5, 1),
        ('E4_Battery', 0.1, 1),
        ('E4_Tag', 0.1, 0)
    ]
    print(f'{len(args)} streams created')
    print(f'streaming started')
    jobs = [emit(*arg) for arg in args]
    conn.DEVICE_ID = '1234567890'
    await asyncio.gather(*jobs)


if __name__ == '__main__':
    try:
        print('starting streaming...')
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print('streaming stopped')
