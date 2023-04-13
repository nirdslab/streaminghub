import logging
from typing import Dict

import pylsl

from .dtypes import Node, Stream

logger = logging.getLogger()


def replay_stream(
    source_id: str,
    stream_id: str,
    source: Node,
    stream: Stream,
    attrs: Dict[str, str],
) -> pylsl.StreamOutlet:
    """
    Generate LSL outlet from Metadata
    :rtype: StreamOutlet
    :param source_id: unique id to identify the source
    :param source: device information (from data-source)
    :param stream_id: id of the stream
    :param stream: stream information (from data-source)
    :param attrs: any additional information (from data-set)
    :return: StreamOutlet object to send data streams through
    """
    info = pylsl.StreamInfo(
        source_id=source_id,
        type=stream_id,  # TODO do not use for queries
        name=f"{source_id}-{stream_id}",  # TODO do not use for queries
        channel_count=len(stream.fields) + len(stream.index),
        nominal_srate=stream.frequency,
    )
    # create stream description
    desc = info.desc()

    # add device information
    if source.device is not None:
        device_info = desc.append_child("device")
        device_info.append_child_value("model", source.device.model)
        device_info.append_child_value("manufacturer", source.device.manufacturer)
        device_info.append_child_value("category", source.device.category)

    # add attributes if present
    attributes = desc.append_child("attributes")
    if attrs and len(attrs.keys()) > 0:
        for attr in attrs.keys():
            attributes.append_child_value(attr, attrs[attr])
    else:
        logger.warning("Creating outlet without attributes")

    # add stream information
    stream_info = desc.append_child("stream")
    stream_info.append_child_value("name", stream.name)
    stream_info.append_child_value("description", stream.description)
    stream_info.append_child_value("unit", stream.unit)
    stream_info.append_child_value("frequency", str(stream.frequency))

    # add field information to stream information
    field_info = stream_info.append_child("channels")
    for field_id in stream.fields.keys():
        field_info = field_info.append_child(field_id)
        # add data field properties
        field = stream.fields[field_id]
        field_info.append_child_value("name", field.name)
        field_info.append_child_value("description", field.description)

    index_info = stream_info.append_child("index")
    for field_id in stream.index.keys():
        field_info = index_info.append_child(field_id)
        # add index field properties
        field = stream.index[field_id]
        field_info.append_child_value("name", field.name)
        field_info.append_child_value("description", field.description)

    # return stream outlet
    return pylsl.StreamOutlet(info)
