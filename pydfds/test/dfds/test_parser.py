import logging
import os
from pathlib import Path

import dfds

logging.basicConfig(level=logging.INFO)


def test_parser():
    parser = dfds.Parser()
    fp = Path(os.getenv("SHUB_META_DIR", "repository")) / "adhd_sin.collection.json"
    fp = fp.resolve().as_posix()
    collection = parser.get_collection_metadata(fp)
    assert collection is not None

    # print all possible recordings, regardless of existence
    for group in collection.iterate_groups():
        print("group=", group)
        for stream_id, stream in collection.streams.items():
            print("stream=", stream_id)
            assert stream is not None

    # print only existing recordings
    dataloader = collection.dataloader()
    for ls_attrs in dataloader.ls():
        attrs, data = dataloader.read(ls_attrs)
        assert data is not None
        assert ls_attrs == attrs
