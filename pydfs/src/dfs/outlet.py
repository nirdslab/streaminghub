import logging
from typing import Dict

import pylsl

from .types import DeviceInfo, StreamInfo

logger = logging.getLogger()


def create_outlet_for_stream(
  source_id: str,
  source: DeviceInfo,
  stream_id: str,
  stream: StreamInfo,
  attrs: Dict[str, str] = None
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
    channel_count=len(stream.channels),
    nominal_srate=stream.frequency
  )
  # create stream description
  desc = info.desc()

  # add device information
  device_info = desc.append_child("device")
  device_info.append_child_value("model", source.model)
  device_info.append_child_value("manufacturer", source.manufacturer)
  device_info.append_child_value("category", source.category)

  # add attributes if present
  attributes = desc.append_child("attributes")
  if attrs and len(attrs.keys()) > 0:
    for attr in attrs.keys():
      attributes.append_child_value(attr, attrs[attr])
  else:
    logger.warning("Creating outlet without attributes")

  # add stream information
  stream_info = desc.append_child("stream")
  # add channel information to stream information
  channels_info = stream_info.append_child("channels")
  for channel_id in stream.channels.keys():
    channel_info = channels_info.append_child(channel_id)
    # add channel properties
    channel_props = stream.channels[channel_id]
    for channel_prop_id in channel_props.keys():
      channel_info.append_child_value(channel_prop_id, channel_props[channel_prop_id])
  # add description and frequency
  stream_info.append_child_value("description", stream.description)
  stream_info.append_child_value("frequency", str(stream.frequency))
  # add indexes information
  stream_idxs_info = stream_info.append_child("index")
  for index_id in stream.index.keys():
    stream_idx_info = stream_idxs_info.append_child(index_id)
    stream_idx_props = stream.index[index_id]
    for stream_idx_prop_id in stream_idx_props.keys():
      stream_idx_info.append_child_value(stream_idx_prop_id, stream_idx_props[stream_idx_prop_id])
  # add name and unit
  stream_info.append_child_value("name", stream.name)
  stream_info.append_child_value("unit", stream.unit)

  # return stream outlet
  return pylsl.StreamOutlet(info)
