#!/usr/bin/env python3

import argparse
import asyncio
import logging
import timeit
from statistics import stdev

import pandas as pd
import streaminghub_datamux as datamux
from rich.logging import RichHandler
from test_configs import data_config, runs
from tqdm import tqdm


async def connect(codec: str, host: str, port: int):
    api = datamux.RemoteAPI("websocket", codec)
    await api.connect(host, port)
    return api


async def timeit_replay(
    api: datamux.RemoteAPI,
    dataset_name: str,
    num_runs: int,
    num_points: int,
    *args,
):
    t_replay = []
    j_replay = []
    iter = tqdm(range(num_runs))
    for _ in iter:
        args = data_config[dataset_name]
        sink = asyncio.Queue()
        _ = await api.list_collections()
        ack = await api.replay_collection_stream(**args, sink=sink)
        assert ack.randseq is not None
        logger.info(f"received ack for collection stream: {ack}")
        start_time = int_time = timeit.default_timer()
        t_jitter = []
        for i in range(num_points + 1):
            item = await sink.get()
            if item == datamux.END_OF_STREAM:
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
        await api.stop_task(ack.randseq)
    return t_replay, j_replay


async def main():
    df = pd.DataFrame()
    parse = argparse.ArgumentParser()
    parse.add_argument("--host", type=str, required=True)
    parse.add_argument("--port", type=int, required=True)
    parse.add_argument("--codec", type=str, required=True)
    args = parse.parse_args()
    api = await connect(args.codec, args.host, args.port)
    for run in runs:
        rows = [[run.dataset_name, run.num_points] for _ in range(run.num_runs)]
        _df = pd.DataFrame(rows, columns=["dataset_name", "num_points"])
        time, jitter = await timeit_replay(api, *run)
        _df["runtime"] = f"rpc_{args.codec}"
        _df["time"] = time
        _df["jitter"] = jitter
        df = pd.concat([df, _df])
    df.index.rename("run", inplace=True)
    df.to_csv(f"stats/run_rpc_{args.codec}.csv")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
