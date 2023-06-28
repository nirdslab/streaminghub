import asyncio
import logging
from typing import List, Dict, Union, Tuple, Any

import numpy as np
import pylsl

from .util import DICT

logger = logging.getLogger()


class RelayMode:
    @staticmethod
    def get_live_streams():
        live_streams = pylsl.resolve_streams()
        return {
            "command": "live_streams",
            "data": {"streams": [*map(RelayMode.gen_stream_info_dict, live_streams)]},
            "error": None,
        }

    @staticmethod
    def sub_live_streams(
        data: List[Dict[str, Union[str, dict]]],
        queue: asyncio.Queue,
    ):
        # source = <source_id> | type = <desc/stream/name>
        stream_query: List[Tuple[str, str, dict]] = [
            (
                str(d.get("source", "")),
                str(d.get("stream", {}).get("name", {})),  # type: ignore
                dict(d.get("attributes", {})),  # type: ignore
            )
            for d in data
        ]
        pred_str = RelayMode.gen_pred_str(stream_query)
        logger.debug("predicate: %s", pred_str)
        # count of queries and tasks
        num_queries = len(stream_query)
        num_tasks = 0
        # run one query to get a superset of the requested streams
        available_live_stream_info: List[pylsl.StreamInfo] = pylsl.resolve_bypred(
            pred_str
        )
        logger.debug(
            "found %d live stream match(es) for predicate",
            len(available_live_stream_info),
        )
        # iterate each query and start live streams
        for live_stream_info in available_live_stream_info:
            # create task to live-stream data
            inlet = pylsl.StreamInlet(live_stream_info, max_chunklen=1, recover=False)
            asyncio.create_task(RelayMode.start_live_stream(inlet, queue))
            num_tasks += 1
        logger.info(
            "started %d live stream tasks for the %d queries", num_tasks, num_queries
        )
        return {
            "command": "notification",
            "data": {
                "message": f"started {num_tasks} live stream tasks for the {num_queries} queries"
            },
            "error": None,
        }

    @staticmethod
    async def start_live_stream(
        stream: pylsl.StreamInlet,
        queue: asyncio.Queue,
    ):
        logger.info("initializing live stream")
        s_info = RelayMode.gen_stream_info_dict(stream)
        logger.info("started live stream")
        while True:
            try:
                samples, timestamps, error = RelayMode.pull_lsl_stream_chunk(stream)
                if error:
                    raise error
                if samples is None or len(samples) == 0:
                    await asyncio.sleep(0.0)
                else:
                    res = {
                        "command": "data",
                        "data": {
                            "stream": {
                                "source": s_info["source"],
                                "mode": s_info["mode"],
                                "attributes": s_info["attributes"],
                                "device": s_info["device"],
                                "stream": s_info["stream"],
                            },
                            "index": timestamps,
                            "chunk": np.nan_to_num(samples, nan=-1).tolist(),
                        },
                    }
                    await queue.put(res)
            except pylsl.LostError:
                break
        logger.info("ended live stream")

    @staticmethod
    def pull_lsl_stream_chunk(
        stream: pylsl.StreamInlet,
        timeout: float = 0.0,
    ):
        try:
            sample, timestamps = stream.pull_chunk(timeout)
            return sample, timestamps, None
        except Exception as e:
            logger.info(f"LSL connection lost")
            return None, None, e

    @staticmethod
    def gen_dict(
        e: pylsl.XMLElement,
        depth=0,
    ) -> Union[DICT, List[Any], str]:
        # terminal case(s)
        if e.empty():
            return {}
        if e.is_text():
            return e.value()
        if e.first_child().is_text():
            return e.first_child().value()
        d = {}
        # parse all children
        child = e.first_child()
        while not child.empty():
            p = RelayMode.gen_dict(child, depth + 1)
            if isinstance(d, dict):
                d[child.name()] = p
            elif isinstance(d, list):
                d.append(p)
            child = child.next_sibling()
        return d

    @staticmethod
    def gen_stream_info_dict(
        x: Union[pylsl.StreamInfo, pylsl.StreamInlet],
    ):
        def fn(i: pylsl.StreamInfo):
            p = RelayMode.gen_dict(i.desc())
            assert isinstance(p, dict)
            return {
                "source": i.source_id(),
                "mode": "live",
                **p,
            }

        if isinstance(x, pylsl.StreamInfo):
            temp_inlet = pylsl.StreamInlet(x)
            result = fn(temp_inlet.info())
            temp_inlet.close_stream()
        elif isinstance(x, pylsl.StreamInlet):
            result = fn(x.info())
        else:
            raise RuntimeError("Invalid object type")
        return result

    @staticmethod
    def gen_pred_str(
        stream_query: List[Tuple[str, str, dict]],
    ):
        partials = []
        for sq_source, sq_name, sq_attrs in stream_query:
            partial = f"source_id='{sq_source}' and desc/stream/name='{sq_name}'"
            if len(sq_attrs) > 0:
                partial += "and " + " and ".join(
                    f"desc/attributes/{x}='{sq_attrs[x]}'" for x in sq_attrs
                )
            partials.append(f"({partial})")
        return " or ".join(partials)
