#!/usr/bin/env python3
from typing import List

import matplotlib
import numpy as np
from matplotlib import pyplot as plt, animation
from pylsl import resolve_stream, StreamInlet

matplotlib.use("Qt5Agg")

streams = resolve_stream('name', 'E4, Empatica (Wristband)')
in_object = [*map(StreamInlet, streams)]


def plot_data(s: List[StreamInlet]):
    S = len(s)
    T = [[]] * S
    D = [[]] * S

    # subplot for each stream inlet
    fig, axs = plt.subplots(S // 2, 2)

    def ax(i):
        return axs if S == 1 else axs[i // 2, i % 2]

    for i in range(S):
        ax(i).title.set_text(s[i].info().type())
    plt.tight_layout()

    def animate(f):
        nonlocal T, D
        for i in range(S):
            T[i] = T[i][-99:] + [f]
            d, _ = s[i].pull_sample(0)
            D[i] = D[i][-99:] + [d or [0] * s[i].channel_count]
            a = ax(i)
            a.clear()
            a.plot(T[i], np.array(D[i]))
            a.title.set_text(s[i].info().type())
            # a.legend()
        plt.tight_layout()

    _ = animation.FuncAnimation(fig, animate, interval=2000)
    plt.show()


if __name__ == '__main__':
    plot_data(in_object)
