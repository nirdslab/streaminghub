#!/usr/bin/env python3

import asyncio
import logging
import multiprocessing
from statistics import stdev
import timeit

import pandas as pd
from rich.logging import RichHandler
from test_configs import data_config, runs
from tqdm import tqdm

import datamux.util as util
from datamux.api import DataMuxAPI


async def connect():
    api = DataMuxAPI()
    return api


async def timeit_replay(
    api: DataMuxAPI,
    dataset_name: str,
    num_runs: int,
    num_points: int,
):
    t_replay = []
    j_replay = []
    iter = tqdm(range(num_runs))
    for _ in iter:
        args = data_config[dataset_name]
        sink = multiprocessing.Queue()
        _ = api.list_collections()
        ack = api.replay_collection_stream(**args, sink=sink)
        assert ack.randseq is not None
        logger.info(f"received ack for collection stream: {ack}")
        start_time = int_time = timeit.default_timer()
        t_jitter = []
        for i in range(num_points + 1):
            item = sink.get()
            if item == util.END_OF_STREAM:
                break
            if i == 0:
                start_time = int_time = timeit.default_timer()
            else:
                t = timeit.default_timer()
                int_time, int_duration = t, (t - int_time)
                t_jitter.append(int_duration)
        end_time = timeit.default_timer()
        duration = end_time - start_time
        jitter = stdev(t_jitter)
        t_replay.append(duration)
        j_replay.append(jitter)
        iter.set_description(f"t={duration:.4f},j={jitter:.4f}")
        api.stop_task(ack.randseq)
    return t_replay, j_replay


async def main():
    df = pd.DataFrame()
    api = await connect()
    for run in runs:
        rows = [[run.dataset_name, run.num_points] for _ in range(run.num_runs)]
        _df = pd.DataFrame(rows, columns=['dataset_name', 'num_points'])
        time, jitter = await timeit_replay(api, *run)
        _df["time"] = time
        _df["jitter"] = jitter
        df = pd.concat([df, _df])
    df.index.rename("run", inplace=True)
    df.to_csv("stats/run_direct.csv")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
