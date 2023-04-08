#!/usr/bin/env python3

import glob
import os

import pandas as pd

import dfds

NOISE_PROFILES = ["p", "b", "n"]
ET_PROFILE = ["ideal", "noisy"]

SRC_DIR = f"{dfds.get_data_dir()}/adhd_sin_synt_orig"
OUT_DIR = f"{dfds.get_data_dir()}/adhd_sin_synt"

if __name__ == '__main__':
  for np in NOISE_PROFILES:
    for ep in ET_PROFILE:
      print(f'Noise Profile: {np}, ET Profile: {ep}')
      files = glob.glob(f"{SRC_DIR}/*-{np}*-{ep}.csv")
      file_names = list(map(os.path.basename, files))
      for file_name in file_names:
        df: pd.DataFrame = pd.read_csv(f'{SRC_DIR}/{file_name}').set_index('t').sort_index()[
          ['fx', 'fy', 'd']].reset_index()
        cols = ['t', 'x', 'y', 'd']
        df.columns = cols
        df = df[cols].round(6).set_index('t')
        # save to file
        os.makedirs(f'{OUT_DIR}_{np}_{ep}', exist_ok=True)
        df.to_csv(f'{OUT_DIR}_{np}_{ep}/{file_name}')
        print(f'Processed: {OUT_DIR}_{np}_{ep}/{file_name}')
