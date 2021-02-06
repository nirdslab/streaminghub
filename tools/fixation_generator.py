#!/usr/bin/env python3
import logging
import sys

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter as sg

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M', level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()

np.set_printoptions(precision=3)

if __name__ == '__main__':
    df = pd.read_csv('../datasets/nback_csv/S1-task-4-2back-center.csv').set_index('t')

    # raw signal
    df_x = np.array(df.x)
    df_y = np.array(df.y)
    df_d = np.array(df.d)

    # sampling freq
    f = 1000 // (df.index[1] - df.index[0])
    # window size
    sg_ws = int((f // 10) + ((f // 10) % 2) - 1)
    # poly order
    sg_po = int(sg_ws // 10)
    logger.debug("Frequency: %f Hz | Window Size: %d Samples | Poly Order: %d", f, sg_ws, sg_po)

    input(df_x.shape)
    df_x_sg = sg(df_x, sg_ws, sg_po)
    df_y_sg = sg(df_y, sg_ws, sg_po)
    df_d_sg = sg(df_d, sg_ws, sg_po)
    # print
    print(df_x)
    print(df_x_sg)
