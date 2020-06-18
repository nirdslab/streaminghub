#!/usr/bin/env python3
import asyncio

from pylsl import StreamInlet, resolve_stream


async def listen(inlet: StreamInlet):
    while True:
        samples, timestamps = inlet.pull_chunk()
        for sample, timestamp in zip(samples, timestamps):
            print('\t'.join(map(lambda x: str(x).ljust(20), [inlet.info().type(), timestamp, sample])), flush=True)
        await asyncio.sleep(0.1)


async def main():
    print("looking for an Empatica E4 stream...")
    streams = resolve_stream('name', 'E4, Empatica (Wristband)')
    assert len(streams) > 0
    print(f'{len(streams)} Stream(s) found!')

    # create a new inlet to read from the stream
    jobs = [listen(StreamInlet(stream)) for stream in streams]
    print('starting listeners')
    await asyncio.gather(*jobs)


if __name__ == '__main__':
    try:
        print('starting listeners...')
        asyncio.run(main())
    except KeyboardInterrupt:
        print('stopped listening')
