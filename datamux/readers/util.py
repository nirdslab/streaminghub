import pylsl
import xmltodict
from dfds.typing import Stream, dtype_map_inv


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
        n_fields_k.append_child_value("dtype", dtype_map_inv[v.dtype])
    # index
    n_index = n_root.append_child("index")
    for k, v in stream.index.items():
        n_index_k = n_index.append_child(k)
        n_index_k.append_child_value("name", v.name)
        n_index_k.append_child_value("description", v.description)
        n_index_k.append_child_value("dtype", dtype_map_inv[v.dtype])
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
    # read stream info in dict format
    inlet = pylsl.StreamInlet(stream_info)
    stream = stream_inlet_to_stream(inlet)
    inlet.close_stream()
    return stream


def stream_inlet_to_stream(
    stream_inlet: pylsl.StreamInlet,
) -> Stream:
    # read stream info in dict format
    info_xml = stream_inlet.info().as_xml()

    # parse stream info
    info: dict = xmltodict.parse(info_xml)["info"]
    desc: dict = info["desc"]
    desc["name"] = info["name"] or ""
    desc["unit"] = info["type"] or ""
    desc["frequency"] = info["nominal_srate"] or ""
    desc["@node"] = desc.pop("node")
    # generate stream object from dict
    return Stream(**desc)

def generate_randstring(length: int = 5):
    import random
    options = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    return ''.join(random.choice(options) for x in range(length))

