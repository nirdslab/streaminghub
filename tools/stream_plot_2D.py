#!/usr/bin/env python3

"""
This command-line executable program accepts a
data-stream name as an input, and generates a
plot for each stream in the data-stream.

It can be used for testing whether a meta-stream
has been correctly used to generate a compliant
data-stream, and also to visualize how different
streams arrive at different frequencies.
"""

import sys
from typing import List

import numpy as np
from pylsl import resolve_stream, StreamInlet

SYNTAX = "stream_plot_2D [stream_name]"


def plot_data(_streams: List[StreamInlet]):
    from matplotlib import pyplot as plt, animation
    S = len(_streams)  # number of streams
    W = 100  # buffer size (only W data points are visualized per plot)
    D = [np.full((W, stream.channel_count), 0.0) for stream in _streams]  # for 2D data (initialize to 0, 0)
    SD = []  # Scatter Data

    COLS = 2
    ROWS = 1 + S // COLS

    # subplot for each stream inlet
    fig, axs = plt.subplots(ROWS, COLS, squeeze=False)

    def ax(_i):
        return axs if S == 1 else axs[_i // COLS, _i % COLS]

    # initialize subplots
    for i in range(S):
        a = ax(i)
        a.xaxis.set_visible(False)
        a.title.set_text(_streams[i].info().type())
        a.set_ylim(0, 1)
        a.set_xlim(0, 1)
        _x = D[i][:, 0]
        _y = D[i][:, 1]
        _c = np.stack([np.zeros(W), np.zeros(W), np.ones(W), np.linspace(0.1, 1.0, W)], axis=-1)
        _s = 2 ** np.linspace(1, 6, W)
        scatters = a.scatter(x=_x, y=_y, s=_s, c=_c, animated=True)
        SD.append(scatters)

    # remove excess subplots
    for i in range(S, ROWS * COLS):
        ax(i).set_axis_off()
    plt.tight_layout()

    def init():
        for _scatters in SD:
            _scatters.set_offsets(np.full((W, 2), 0.0))
        return SD

    def animate(f):
        nonlocal D
        for _i in range(S):
            _si = _streams[_i]
            samples, _ = _si.pull_chunk(max_samples=1024)
            _n = len(samples)
            if _n == 0:
                continue

            # convert samples to numpy array, and move nan values outside visible plot range
            samples = np.nan_to_num(np.array(samples), nan=-1.0)

            # update samples
            if _n < W:
                d_i = np.roll(D[_i], -_n, axis=0)
                d_i[-_n:] = samples
                D[_i] = d_i.copy()
            else:
                D[_i] = np.array(samples[-W:]).copy()
            # update plot
            _cc = _si.channel_count
            SD[_i].set_offsets(D[_i])
        return SD

    # _ = animation.FuncAnimation(fig, animate, init_func=init, blit=True, interval=100)
    _ = animation.FuncAnimation(fig, animate, init_func=init, blit=True, save_count=0, cache_frame_data=False)
    plt.show()


def main():
    # Load matplotlib
    import matplotlib
    matplotlib.use("Qt5Agg")
    # parse command-line args
    args = sys.argv
    assert len(args) == 2, f"Invalid Syntax.\nExpected: {SYNTAX}"
    stream_name = sys.argv[1]
    streams = resolve_stream('name', stream_name)
    streams = filter(lambda x: x.channel_count() == 2, streams)
    in_object = [*map(StreamInlet, streams)]
    plot_data(in_object)


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
