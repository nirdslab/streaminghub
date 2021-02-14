#!/usr/bin/env python3

import glob
import os

import pandas as pd

SRC_DIR = "../datasets/adhd_sin_orig"
OUT_DIR = "../datasets/adhd_sin"

if __name__ == '__main__':
    files = glob.glob(f"{SRC_DIR}/*.csv")
    file_names = list(map(os.path.basename, files))
    for file_name in file_names:
        df: pd.DataFrame = pd.read_csv(f'{SRC_DIR}/{file_name}').set_index('EyeTrackerTimestamp')[['GazePointX (ADCSpx)', 'GazePointY (ADCSpx)', 'PupilLeft', 'PupilRight']].sort_index().reset_index()
        df.columns = ['t', 'x', 'y', 'dl', 'dr']
        # fill blanks (order=interpolate(inter)->bfill+ffill(edges))->zerofill
        df = df.apply(lambda x: x.interpolate().fillna(method="bfill").fillna(method="ffill")).fillna(0)
        df['x'] = df['x'] / 1920
        df['y'] = df['y'] / 1080
        df['d'] = (df['dl'] + df['dr']) / 2
        # start with t=0, and set unit to ms
        df['t'] = (df['t'] - df['t'].min()) / 1000
        df = df[['t', 'x', 'y', 'd']].round(6).set_index('t')
        df.to_csv(f'{OUT_DIR}/{file_name}')
        print(f'Processed: {file_name}')
