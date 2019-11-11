"""Example program to demonstrate how to send a multi-channel time series to
LSL."""

import random
import time

from pylsl import StreamInfo, StreamOutlet

# first create a new stream info (here we set the name to BioSemi,
# the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
# last value would be the serial number of the device or some other more or
# less locally unique identifier for the stream as far as available (you
# could also omit it but interrupted connections wouldn't auto-recover).
info_8ch = StreamInfo('BioSemi', 'EEG', 8, 100, 'float32', 'biosemieeg12345')
info_16ch = StreamInfo('EmotivPro', 'EEG', 16, 100, 'float32', 'emotivpro12345')

# next make an outlet
outlet_s1 = StreamOutlet(info_8ch)
outlet_s2 = StreamOutlet(info_16ch)

if __name__ == '__main__':
    print("now sending data...")
    while True:
        # make a new random 8-channel sample; this is converted into a
        # pylsl.vectorf (the data type that is expected by push_sample)
        mysample = [random.random() for x in range(16)]
        # now send it and wait for a bit
        outlet_s1.push_sample(mysample[4:12])
        outlet_s2.push_sample(mysample[:16])
        time.sleep(0.01)
