import pylsl
import streaminghub_pydfds as dfds


def stream_to_stream_info(
    stream: dfds.Stream,
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
        n_fields_k.append_child_value("dtype", dfds.dtype_map_inv[v.dtype])
    # index
    n_index = n_root.append_child("index")
    for k, v in stream.index.items():
        n_index_k = n_index.append_child(k)
        n_index_k.append_child_value("name", v.name)
        n_index_k.append_child_value("description", v.description)
        n_index_k.append_child_value("dtype", dfds.dtype_map_inv[v.dtype])
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
