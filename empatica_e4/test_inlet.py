#!/usr/bin/env python3

from pylsl import StreamInlet, resolve_stream

if __name__ == '__main__':
    print("looking for an Empatica E4 stream...")
    streams = resolve_stream('name', 'Empatica E4')
    assert len(streams) > 0
    print(f'{len(streams)} Stream(s) found!')

    # create a new inlet to read from the stream
    inlets = []
    for stream in streams:
        inlets.append(StreamInlet(stream))

    while True:
        # get a new sample (you can also omit the timestamp part if you're not interested in it)
        for inlet in inlets:
            sample, timestamp = inlet.pull_sample(0)
            if timestamp is not None:
                print('\t'.join(map(str,[inlet.info().type()[:3], timestamp, sample])))
