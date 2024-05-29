#!/usr/bin/env python3

"""
Example of Streaming Data from Pupil Labs Core
over StreamingHub

"""

import logging

import streaminghub_datamux as datamux


def main():

    api = datamux.API()
    sink = datamux.Queue()

    node_id = "pupil_core"

    streams = api.list_live_streams(node_id)
    assert len(streams) >= 1

    stream = streams[0]
    stream_id = stream.name
    attrs = stream.attrs

    ack = api.proxy_live_stream(node_id, stream_id, attrs, sink=sink)
    assert ack.randseq is not None

    while True:
        item = sink.get()
        logger.info(f"received item: {item}")
        if item == datamux.END_OF_STREAM:
            break
    api.stop_task(ack.randseq)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]")
    logger = logging.getLogger(__name__)
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupt received, shutting down.")
