#!/usr/bin/env python3
import sys
from typing import List

import numpy as np
from pylsl import resolve_stream, StreamInlet

SYNTAX = "data-stream-plot [stream_name]"


def plot_data(_streams: List[StreamInlet]):
    from matplotlib import pyplot as plt, animation
    S = len(_streams)  # number of streams
    W = 100  # buffer size (only W data points are visualized per plot)
    T = [np.arange(W) for _ in _streams]  # for timestamps (initialize to nan)
    D = [np.full((W, stream.channel_count), np.nan) for stream in _streams]  # for data (initialize to nan)
    L = []

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
        a.set_ylim(-1, 1)
        a.set_xlim(0, W)
        lines = a.plot(T[i], np.array(D[i]), '-d', markersize=2, animated=True)
        L.append(lines)
    # remove excess subplots
    for i in range(S, ROWS * COLS):
        ax(i).set_axis_off()
    plt.tight_layout()

    def init():
        for _lines in L:
            for _line in _lines:
                _line.set_ydata(np.full((W,), np.nan))
        return [y for x in L for y in x]

    def animate(f):
        nonlocal D
        for _i in range(S):
            _si = _streams[_i]
            samples, _ = _si.pull_chunk(max_samples=1024)
            _n = len(samples)
            if _n == 0:
                continue
            # update samples
            elif _n < W:
                d_i = np.roll(D[_i], -_n, axis=0)
                d_i[-_n:] = np.array(samples)
                D[_i] = d_i
            else:
                D[_i] = np.array(samples)[-W:]
            # update plot
            _cc = _si.channel_count
            for c in range(_cc):
                L[_i][c].set_ydata(D[_i][:, c])
        return [y for x in L for y in x]

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
    in_object = [*map(StreamInlet, streams)]
    plot_data(in_object)


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'Error: {e}', file=sys.stderr)
