import pandas as pd
import json
from pathlib import Path
import numpy as np

import streaminghub_pydfds as dfds

pd.set_option('display.max_rows', int(1e9))
pd.set_option('display.max_columns', int(1e9))


if __name__ == "__main__":
    cols = ["t", "x", "y"]
    base_path = Path(__file__).with_name("generated")
    for fp in sorted(base_path.glob("*/*.log")):
        dir_name = fp.parent.name
        file_name = fp.name

        subject, noise, task = dir_name.split("_")
        simulation, vt = file_name.split("_")
        print(subject, noise, task, simulation, vt)

        with open(fp) as f:
            recs = [json.loads(line) for line in f.readlines()]
        rcn_df = pd.DataFrame(recs)[cols]
        rcn_df['dt'] = rcn_df['t'].diff().mean()
        print(rcn_df)

        # source dataset
        src_dir = dfds.load_config().data_dir
        src_fp = src_dir / "ADHD_SIN" / f"{subject}_{noise}_{task}.parquet"
        reader = dfds.create_reader(src_fp)
        src_meta, src_df = reader.read(rec_path=".")
        src_df["x"] = (src_df["lx"] + src_df["rx"]) / 2
        src_df["y"] = (src_df["ly"] + src_df["ry"]) / 2
        src_df["t"] = (src_df["t"] - src_df["t"].iloc[0]) / 1e6
        src_df = src_df[cols]
        src_df['dt'] = src_df['t'].diff().mean()
        print(src_df)
        exit(0)
    # df = pd.DataFrame()