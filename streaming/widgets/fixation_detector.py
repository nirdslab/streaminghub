import math
import typing
from queue import Queue
from typing import List

import numpy as np
from AnyQt.QtCore import Signal
from Orange.data import Table, TimeVariable, ContinuousVariable, Domain
from PyQt5.QtCore import QThread, QObject

PI = 22 / 7
RAD2DEG = 360 / (PI ** 2)
COEFFICIENTS = [0.10714286, 0.07142857, 0.03571429, 0, -0.03571429, -0.07142857, -0.10714286]
BUF_SIZE = 7


class FixationDetector(QThread):
    """
    Detect fixations in real-time
    """

    xCoordinates: Queue
    yCoordinates: Queue
    output = Signal(Table)

    def __init__(self, job, s_rate: float = 128.0, D_in: float = 20.0, screen_w_px: int = 1440, screen_h_px: int = 900,
                 screen_diag_in: float = 13.3, parent: typing.Optional[QObject] = None) -> None:
        """
        Create Instance

        :param s_rate: sampling rate (Hz)
        :param D_in: distance to monitor display (inches)
        :param screen_w_px: screen width (pixels)
        :param screen_h_px: screen height (pixels)
        :param screen_diag_in: screen diagonal length (inches)
        """
        super().__init__(parent)
        self.job = job
        self.period = 1000.0 / s_rate
        self.D_in = D_in
        self.screen_w_px = screen_w_px
        self.screen_h_px = screen_h_px
        self.screen_diag_in = screen_diag_in
        self.xCoordinates = Queue()
        self.yCoordinates = Queue()

    def clear(self):
        self.xCoordinates = Queue()
        self.yCoordinates = Queue()

    def next(self, x_norm_pos, y_norm_pos):
        """
        Update is called once per frame
        """
        # push gaze coordinates into queue
        x_coord = int(x_norm_pos * self.screen_w_px)
        y_coord = int(y_norm_pos * self.screen_h_px)
        self.xCoordinates.put(x_coord)
        self.yCoordinates.put(y_coord)

        # no fixations detected until the coordinate buffer has ${BUF_SIZE} values
        if self.xCoordinates.qsize() < BUF_SIZE:
            return False

        # reduce buffer sizes to ${BUF_SIZE}
        while self.xCoordinates.qsize() > BUF_SIZE:
            self.xCoordinates.get()
        while self.yCoordinates.qsize() > BUF_SIZE:
            self.xCoordinates.get()

        # fixation arrays, size = 11
        fxn_x = convolve(COEFFICIENTS, list(self.xCoordinates.queue))
        fxn_y = convolve(COEFFICIENTS, list(self.yCoordinates.queue))

        # screen diagonal size
        r = math.sqrt(self.screen_w_px ** 2 + self.screen_h_px ** 2)
        dpi = r / self.screen_diag_in

        deg_x = 2.0 * RAD2DEG * math.atan2((fxn_x[6] / dpi), (2.0 * self.D_in))
        deg_y = 2.0 * RAD2DEG * math.atan2((fxn_y[6] / dpi), (2.0 * self.D_in))

        # dt is how much time used in convolution calculation:
        # period in seconds * number of samples (as many as filter len)
        dt = self.period / 1000.0 * BUF_SIZE

        vel_x = deg_x / dt
        vel_y = deg_y / dt
        vel = math.sqrt(vel_x ** 2 + vel_y ** 2)

        if vel <= 8:
            return True
        else:
            return False

    def run(self) -> None:
        if self.job is not None:
            [t, x_norm_pos, y_norm_pos] = self.job
            fxn = []
            for i in range(len(x_norm_pos)):
                fxn.append(self.next(x_norm_pos[i], y_norm_pos[i]))
            fxn = np.array(fxn)
            table = Table.from_numpy(Domain([TimeVariable('t'), ContinuousVariable('fxn')]), np.stack([t, fxn], axis=-1))
            self.output.emit(table)


def convolve(u: List[float], v: List[float]) -> List[float]:
    reversed_v = list(reversed(v))
    size_v = len(reversed_v) - 1
    nArray = [0.0] * size_v
    pad = concat_arrays(nArray, u, nArray)

    m = len(u)
    n = len(v)
    k = m + n - 1
    w = [0.0] * k

    for i in range(k):
        for j in range(n):
            w[i] += pad[i + j] * reversed_v[j]
    return w


def concat_arrays(*args):
    result = []
    for x in range(len(args)):
        result.extend(args[x])
    return result
