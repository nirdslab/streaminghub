#!/usr/bin/env python3
from pylsl import StreamInlet, resolve_stream

# first resolve an EEG stream on the lab network
print("looking for an Empatica E4 stream...")
streams = resolve_stream('type', 'wristband')

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

while True:
    # get a new sample (you can also omit the timestamp part if you're not interested in it)
    sample, timestamp = inlet.pull_sample()
    print(timestamp, sample)
