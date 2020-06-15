from pylsl import StreamInfo, StreamOutlet

from core.types import MetaStream


def create_outlet(source_id: str, meta: MetaStream, idx: int) -> StreamOutlet:
    """
    Generate LSL outlet from Metadata
    :rtype: StreamOutlet
    :param source_id: id for the device, usually the manufacturer and device type combined
    :param meta: meta stream (description of all streams from a particular device)
    :param idx: which stream, from all streams in meta, to create an outlet for
    :return: StreamOutlet object to send data streams through
    """
    stream: MetaStream.StreamInfo = meta.streams[idx]
    info = StreamInfo(
        source_id=source_id,
        name=f'{meta.device.model}, {meta.device.manufacturer} ({meta.device.category})',
        type=stream.name,
        channel_count=len(stream.channels),
        nominal_srate=stream.frequency
    )
    # create stream description
    desc = info.desc()
    desc.append_child_value("unit", stream.unit)
    desc.append_child_value("freq", str(stream.frequency))
    channels = desc.append_child("channels")
    for channel in stream.channels:
        channels.append_child_value("channel", channel)
    # return stream outlet
    return StreamOutlet(info)
