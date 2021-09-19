#!/usr/bin/env python3

import glob
import os

import pandas as pd

import dfs

SRC_DIR = f"{dfs.get_data_dir()}/n_back_orig"
OUT_DIR = f"{dfs.get_data_dir()}/n_back"

if __name__ == '__main__':
  files = glob.glob(f"{SRC_DIR}/*.csv")
  file_names = list(map(os.path.basename, files))
  for file_name in file_names:
    df = pd.read_csv(f'{SRC_DIR}/{file_name}').set_index('t').sort_index()[['x', 'y', 'd']].reset_index()
    # fill blanks (order=interpolate(inter)->bfill+ffill(edges))->zerofill
    df = df.apply(lambda x: x.interpolate().fillna(method="bfill").fillna(method="ffill")).fillna(0)
    # start with t=0
    df['t'] = df['t'] - df['t'].min()
    df = df.round(6).set_index('t')
    df.to_csv(f'{OUT_DIR}/{file_name}')
    print(f'Processed: {file_name}')
