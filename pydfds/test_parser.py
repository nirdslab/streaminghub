import logging

import src as dfds

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    parser = dfds.Parser()
    collection = parser.get_collection_metadata(
        "../dfds/samples/running_metrics.collection.json"
    )
    for stream_id, stream in collection.streams.items():
        print(stream_id)
        # outlet = replay_stream(
        #     source_id="12345",
        #     stream_id=stream_id,
        #     source=,
        #     stream=stream,
        #     attrs=,
        # )
