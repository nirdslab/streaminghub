from pylsl import StreamInfo, StreamOutlet

from core.types import MetaStream


def create_outlet(source_id: str, device: MetaStream.DeviceInfo, stream: MetaStream.StreamInfo) -> StreamOutlet:
    """
    Generate LSL outlet from Metadata
    :rtype: StreamOutlet
    :param source_id: id for the device, usually the manufacturer and device type combined
    :param device: device information (from meta-stream)
    :param stream: stream information (from meta-stream)
    :return: StreamOutlet object to send data streams through
    """
    info = StreamInfo(
        source_id=source_id,
        name=f'{device.model}, {device.manufacturer} ({device.category})',
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
