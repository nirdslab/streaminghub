from pylsl import StreamInfo, StreamOutlet

from core.types import DeviceDesc, StreamDesc


def create_outlet(source_id: str, device_desc: DeviceDesc, stream_desc: StreamDesc) -> StreamOutlet:
    """
    Generate LSL outlet from Metadata
    :rtype: StreamOutlet
    :param source_id: id for the device, usually the manufacturer and device type combined
    :param device_desc: device information (name, type)
    :param stream_desc: stream description. should contain the keys (name, unit, freq, channel_count, channels)
    :return: StreamOutlet object to send data streams through
    """
    info = StreamInfo(
        source_id=source_id,
        name=device_desc.name,
        type=stream_desc.name,
        channel_count=stream_desc.channel_count,
        nominal_srate=stream_desc.freq
    )
    # create stream description
    desc = info.desc()
    desc.append_child_value("unit", stream_desc.unit)
    desc.append_child_value("freq", str(stream_desc.freq))
    channels = desc.append_child("channels")
    for channel in stream_desc.channels:
        channels.append_child_value("channel", channel)
    # return stream outlet
    return StreamOutlet(info)
