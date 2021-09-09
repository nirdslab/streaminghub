import os
from glob import glob

import numpy as np
import pandas as pd

DATASET_NAME = "adhd_sin"
DATASET_PATH = f"../datasets/{DATASET_NAME}"

REFN_DATA_PATH = f"{DATASET_PATH}"  # reference data
REFN_FXTN_PATH = f"{REFN_DATA_PATH}_fxtn"  # fixations from reference data
SYNT_DATA_PATH = f"{DATASET_PATH}_synt"  # synthetic data
SYNT_FXTN_PATH = f"{SYNT_DATA_PATH}_fxtn"  # fixations from synthetic data


# ax = [1,2,3,4,5,6,7]
# ay = [2,3,4,5,6,7,8]
# bx = [2,3,4]
# by = [3,4,5]


def calculate_rmse(a: np.ndarray, b: np.ndarray):
  # keep ax,ay as longer array
  na = a.shape[0]
  nb = b.shape[0]
  if a.shape[0] < b.shape[0]:
    a, b, na, nb = b, a, nb, na
  # extend b to fit a
  b = np.column_stack([
    np.interp(np.linspace(0, nb - 1, na), np.arange(nb), b[:, 0]),
    np.interp(np.linspace(0, nb - 1, na), np.arange(nb), b[:, 1])
  ])
  # return rmse
  return np.sqrt(np.mean(np.sum(np.square(a - b), axis=1))), na


def adhd_sin_filename_parse(part: str):
  pid = part[:3]
  p2 = part[11:]
  possible_noise_levels = ['0', '5', '10', '15', '20', '25']
  if p2[0] in possible_noise_levels:
    return [pid, p2[0], p2[1:]]
  elif p2[:2] in possible_noise_levels:
    return [pid, p2[:2], p2[2:]]
  else:
    raise RuntimeError("Filename cannot be parsed", part)


if __name__ == '__main__':
  synt_data_glob = glob(f"{SYNT_DATA_PATH}/*.csv")
  # print(f"{len(synt_data_glob)} synthetic data files found")
  synt_fxtn_glob = glob(f"{SYNT_FXTN_PATH}/*.csv")
  # print(f"{len(synt_data_glob)} synthetic fixation files found")
  cols = []
  stats_cols = ["noise_model", "tracker_model", "rmse", "points"]
  df: pd.DataFrame
  if DATASET_NAME == "n_back":
    cols = ["participant", "mode", "task", "position", *stats_cols]
  if DATASET_NAME == "adhd_sin":
    cols = ["participant", "noise", "question", *stats_cols]
  df = pd.DataFrame(columns=cols)
  # compare reference [data] against synthetic [data]
  for synt_data_fp in synt_data_glob:
    (file_name, file_ext) = os.path.splitext(os.path.basename(synt_data_fp))
    parts = file_name.split('-')
    file_parts = [*parts[:-2], parts[-1]]
    if DATASET_NAME == "adhd_sin":
      file_parts = [*adhd_sin_filename_parse(file_parts[0]), *file_parts[1:]]
    refn_data_fp = f"{REFN_DATA_PATH}/{file_name.rsplit('-', 3)[0]}{file_ext}"
    # print(f'Comparing: {synt_data_fp} against {refn_data_fp}')
    # opening synthetic and reference files
    synt_df = pd.read_csv(synt_data_fp, index_col='t')[['fx', 'fy']]
    synt_df.columns = ['x', 'y']
    refn_df = pd.read_csv(refn_data_fp, index_col='t')[['x', 'y']]
    refn_df.index = refn_df.index / 1000.0
    s = synt_df[['x', 'y']].to_numpy()
    r = refn_df[['x', 'y']].to_numpy()
    rmse, points = calculate_rmse(s, r)
    row = [*file_parts, rmse, points]
    df.loc[len(df.index)] = row
    print(row)
  df.set_index(df.columns[0]).to_csv(f"../comparisons/{DATASET_NAME}_synt_data_comparison.csv")

# # compare reference [fxtn] against synthetic [fxtn]
# for synt_fxtn_fp in synt_fxtn_glob:
#     (file_name, file_ext) = os.path.splitext(os.path.basename(synt_fxtn_fp))
#     refn_fxtn_fp = f"{REFN_FXTN_PATH}/{file_name.rsplit('-', 3)[0]}{file_ext}"
#     print(f'Comparing: {synt_fxtn_fp} against {refn_fxtn_fp}')
#     # opening synthetic and reference files
#     synt_df = pd.read_csv(synt_fxtn_fp, index_col='t')
#     refn_df = pd.read_csv(refn_fxtn_fp, index_col='t')
