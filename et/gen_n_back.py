#!/usr/bin/env python3

import glob
import os

import pandas as pd

SRC_DIR = "../datasets/n_back_orig"
OUT_DIR = "../datasets/n_back"

if __name__ == '__main__':
    files = glob.glob(f"{SRC_DIR}/*.csv")
    file_names = list(map(os.path.basename, files))
    for file_name in file_names:
        df = pd.read_csv(f'{SRC_DIR}/{file_name}').set_index('t')[['x', 'y', 'd']].sort_index().reset_index()
        # fill blanks (order=interpolate(inter)->bfill+ffill(edges))
        df = df.apply(lambda x: x.interpolate().fillna(method="bfill").fillna(method="ffill"))
        # start with t=0
        df['t'] = df['t'] - df['t'].min()
        df = df.round(4).set_index('t')
        df.to_csv(f'{OUT_DIR}/{file_name}')
        print(f'Processed: {file_name}')
