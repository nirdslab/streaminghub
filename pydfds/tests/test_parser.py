import logging

import src as dfds
from src.dtypes import Node

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    parser = dfds.Parser()
    collection = parser.get_collection_metadata(
        "../dfds/samples/running_metrics.collection.json"
    )
    node: Node
    for stream_id, stream in collection.streams.items():
        node = stream.node
        assert node is not None
        print(stream_id, stream, node)
        outlet = dfds.replay_stream(
            stream_id=stream_id,
            stream=stream,
            attrs={},
        )
