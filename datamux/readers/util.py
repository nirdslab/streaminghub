from typing import OrderedDict

import pylsl
from dfds.typing import Field, Stream


def stream_to_stream_info(
    stream: Stream,
) -> pylsl.StreamInfo:
    node = stream.node
    assert node
    device = node.device
    if device:
        stream_type = device.category
    else:
        stream_type = "unknown"
    stream_info = pylsl.StreamInfo(
        name=stream.name,
        type=stream_type,
        channel_count=len(stream.fields),
        nominal_srate=stream.frequency,
        channel_format=pylsl.cf_float32,
    )
    desc = stream_info.desc()
    for k, v in stream.attrs.values():
        desc.append_child_value(k, v)
    return stream_info


def stream_info_to_stream(
    stream_info: pylsl.StreamInfo,
) -> Stream:
    items = stream_info_to_dict(stream_info)
    data = {
        "@node": None,
        "name": items["name"],
        "description": items["description"],
        "unit": items["unit"],
        "frequency": items["frequency"],
        "fields": OrderedDict([(k, Field(**v)) for k, v in items["fields"].items()]),
        "index": OrderedDict([(k, Field(**v)) for k, v in items["index"].items()]),
        "attrs": {},
    }
    return Stream(**data)


def xml_to_dict(
    e: pylsl.XMLElement,
) -> dict:
    # text node - return value
    if e.is_text():
        return e.value()
    # xml node - recurse children
    key = e.name()
    value = {}
    child = e.first_child()
    while not child.empty():
        k, v = child.name(), xml_to_dict(child)
        if k not in value:
            value[k] = v
        elif not isinstance(value[k], list):
            value[k] = [value[k], v]
        else:
            value[k].append(v)
        child = child.next_sibling()
    return {key: value}


def stream_info_to_dict(
    stream_info: pylsl.StreamInfo,
) -> dict:
    # TODO if streams contain node metadata, read them.
    # TODO otherwise, fetch them from repository.
    # TODO update with correct stream metadata

    inlet = pylsl.StreamInlet(stream_info)
    complete_stream_info = inlet.info()
    source_id = complete_stream_info.source_id()
    items = xml_to_dict(complete_stream_info.desc())
    inlet.close_stream()
    return {
        "source_id": source_id,
        **items,
    }
