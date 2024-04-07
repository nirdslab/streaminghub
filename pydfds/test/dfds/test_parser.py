import logging

import streaminghub_pydfds as dfds

logging.basicConfig(level=logging.INFO)


def test_parser():
    parser = dfds.Parser()
    config = dfds.load_config()

    fp = config.meta_dir / "adhd_sin.collection.json"
    collection = parser.get_collection_metadata(fp.as_posix())
    assert collection is not None

    # print all possible recordings, regardless of existence
    for group in collection.iterate_groups():
        print("group=", group)
        for stream_id, stream in collection.streams.items():
            print("stream=", stream_id)
            assert stream is not None

    # print only existing recordings
    dataloader = collection.dataloader(config)
    for ls_attrs in dataloader.ls():
        attrs, data = dataloader.read(ls_attrs)
        assert data is not None
        assert ls_attrs == attrs
