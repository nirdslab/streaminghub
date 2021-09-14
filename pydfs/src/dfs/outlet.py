import logging
from typing import Dict

from pylsl import StreamInfo as LSLStreamInfo, StreamOutlet as LSLStreamOutlet

from .types import DeviceInfo, StreamInfo

logger = logging.getLogger()


def create_outlet_for_stream(
  source_id: str,
  source: DeviceInfo,
  stream_id: str,
  stream: StreamInfo,
  attrs: Dict[str, str] = None
) -> LSLStreamOutlet:
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
  name = f'{source.manufacturer} {source.model}'
  source_id = f'{name} [{source_id}]'
  info = LSLStreamInfo(
    source_id=source_id,
    type=stream_id,
    name=name,
    channel_count=len(stream.channels),
    nominal_srate=stream.frequency
  )
  # create stream description
  desc = info.desc()
  desc.append_child_value("unit", stream.unit)
  desc.append_child_value("freq", str(stream.frequency))
  # add device information
  device_info = desc.append_child("device")
  device_info.append_child_value("model", source.model)
  device_info.append_child_value("manufacturer", source.manufacturer)
  device_info.append_child_value("category", source.category)
  channels_info = desc.append_child("channels")
  for channel in stream.channels.keys():
    channels_info.append_child_value("channel", channel)
  # append attrs if present
  if attrs and len(attrs.keys()) > 0:
    attributes_info = desc.append_child("attributes")
    for attr in attrs.keys():
      attributes_info.append_child_value(attr, attrs[attr])
  else:
    logger.warning("Creating outlet without attributes")
  # return stream outlet
  return LSLStreamOutlet(info)
