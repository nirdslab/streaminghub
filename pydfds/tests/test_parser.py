import logging

import dfds

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = dfds.Parser()
    collection = parser.get_collection_metadata(
        "../dfds/samples/running_metrics.collection.json"
    )

    for group in collection.iterate_groups():
        for stream_id, stream in collection.streams.items():
            assert stream.node
            stream.attrs = group
            print(stream_id, stream.attrs)
            outlet = dfds.create_outlet(
                stream_id=stream_id,
                stream=stream,
            )

    # dataloader = collection.dataloader()
    # for attrs in dataloader.ls():
    #     attrs, data = dataloader.read(attrs)
    #     print(attrs, data.shape)
