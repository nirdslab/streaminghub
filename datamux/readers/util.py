import pylsl
from dfds.typing import Stream


def stream_to_stream_info(
    stream: Stream,
) -> pylsl.StreamInfo:
    stream_info = pylsl.StreamInfo(
        name=stream.name,
        type=stream.unit,
        channel_count=len(stream.fields),
        nominal_srate=stream.frequency,
        channel_format=pylsl.cf_float32,
    )
    n_root = stream_info.desc()
    # description
    n_root.append_child_value("description", stream.description)
    # fields
    n_fields = n_root.append_child("fields")
    for k, v in stream.fields.items():
        n_fields_k = n_fields.append_child(k)
        n_fields_k.append_child_value("name", v.name)
        n_fields_k.append_child_value("description", v.description)
        n_fields_k.append_child_value("dtype", v.dtype.__name__)
    # index
    n_index = n_root.append_child("index")
    for k, v in stream.index.items():
        n_index_k = n_index.append_child(k)
        n_index_k.append_child_value("name", v.name)
        n_index_k.append_child_value("description", v.description)
        n_index_k.append_child_value("dtype", v.dtype.__name__)
    # attrs
    n_attrs = n_root.append_child("attrs")
    for k, v in stream.attrs.items():
        n_attrs.append_child_value(k, v)
    # device
    assert stream.node
    n_node = n_root.append_child("node")
    if stream.node.device:
        device = stream.node.device
        n_node_device = n_node.append_child("device")
        n_node_device.append_child_value("category", device.category)
        n_node_device.append_child_value("manufacturer", device.manufacturer)
        n_node_device.append_child_value("model", device.model)
    return stream_info


def stream_info_to_stream(
    stream_info: pylsl.StreamInfo,
) -> Stream:
    # stream dict
    # read stream info in dict format
    temp_inlet = pylsl.StreamInlet(stream_info)
    full_stream_info = temp_inlet.info()
    # parse stream desc()
    desc = __xml_to_dict(full_stream_info.desc())
    desc["name"] = full_stream_info.name()
    desc["unit"] = full_stream_info.type()
    desc["frequency"] = full_stream_info.nominal_srate()
    desc["@node"] = desc.pop("node")
    temp_inlet.close_stream()
    # generate stream object from dict
    return Stream(**desc)


def __xml_to_dict(
    e: pylsl.XMLElement,
) -> dict:
    """
    Converts LSL XML metadata into a dictionary

    Args:
        e (pylsl.XMLElement): LSL XML metadata

    Returns:
        dict: the extracted dictionary from LSL XML metadata
    """

    # text node - return value
    if e.is_text():
        return e.value()
    # xml node - gather all children
    key = e.name()
    children = []
    child = e.first_child()
    while not child.empty():
        children.append(child)
        child = child.next_sibling()

    value = {}
    for child in children:
        k, v = child.name(), __xml_to_dict(child)
        if k not in value:
            value[k] = v
        elif not isinstance(value[k], list):
            value[k] = [value[k], v]
        else:
            value[k].append(v)

    # remove redundant nodes
    if len(value) == 1:
        value = list(value.values())[0]

    return {key: value}
