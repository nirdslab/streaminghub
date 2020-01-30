import time

import numpy as np
from pylsl import StreamInfo, StreamOutlet

# 100 Hz
SAMPLING_FREQ = 100

if __name__ == '__main__':
    # define streams
    streams = [
        StreamInfo('BioSemi', 'EEG', 8, SAMPLING_FREQ, 'float32', 'biosemieeg12345'),
        StreamInfo('EmotivPro', 'EEG', 16, SAMPLING_FREQ, 'float32', 'emotivpro12345')
    ]
    # make outlets
    outlets = list(map(StreamOutlet, streams))
    # start sending data
    print("sending data started...")
    while True:
        # push random data from all outlets
        for o in outlets:
            o.push_sample(np.random.random(o.channel_count))
        # sleep to match the sampling frequency
        time.sleep(1 / SAMPLING_FREQ)
