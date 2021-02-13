import logging
from typing import Dict, Any

from pylsl import StreamInfo as LSLStreamInfo, StreamOutlet as LSLStreamOutlet

from core.types import DeviceInfo, StreamInfo

logger = logging.getLogger()


def create_outlet(source_id: str, device: DeviceInfo, stream: StreamInfo, attrs: Dict[str, str] = None) -> LSLStreamOutlet:
    """
    Generate LSL outlet from Metadata
    :rtype: StreamOutlet
    :param source_id: id for the device, usually the manufacturer and device type combined
    :param device: device information (from data-source)
    :param stream: stream information (from data-source)
    :param attrs: any additional information (from data-set)
    :return: StreamOutlet object to send data streams through
    """
    info = LSLStreamInfo(
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
    for channel in stream.channels.keys():
        channels.append_child_value("channel", channel)
    # append attrs if present
    if attrs and len(attrs.keys()) > 0:
        attributes = desc.append_child("attributes")
        for attr in attrs.keys():
            attributes.append_child_value(attr, attrs[attr])
    else:
        logger.warning("Creating outlet without attributes")
    # return stream outlet
    return LSLStreamOutlet(info)
