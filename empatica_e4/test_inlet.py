#!/usr/bin/env python3
from threading import Thread
from time import sleep

from pylsl import StreamInlet, resolve_stream


def listener(inlet):
    while True:
        sample, timestamp = inlet.pull_sample()
        print('\t'.join(map(lambda x: str(x).ljust(20), [inlet.info().type(), timestamp, sample])), flush=True)
        sleep(1)


if __name__ == '__main__':
    print("looking for an Empatica E4 stream...")
    streams = resolve_stream('name', 'Empatica E4')
    assert len(streams) > 0
    print(f'{len(streams)} Stream(s) found!')

    # create a new inlet to read from the stream
    threads = list(map(lambda x: Thread(target=listener, args=(StreamInlet(x),)), streams))
    print('starting listeners')
    for thread in threads:
        thread.start()
    threads[0].join()
