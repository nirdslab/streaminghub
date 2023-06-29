import logging

import dfds

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = dfds.Parser()
    collection = parser.get_collection_metadata("repository/adhd_sin.collection.json")

    for group in collection.iterate_groups():
        for stream_id, stream in collection.streams.items():
            print(stream_id, dict(group))

    dataloader = collection.dataloader()
    for ls_attrs in dataloader.ls():
        attrs, data = dataloader.read(ls_attrs)
        assert ls_attrs == attrs
        print(attrs)
        print(data.shape, data.dtype.names, "\n")
