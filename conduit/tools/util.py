from typing import Dict, Any, Union, List

from pylsl import StreamInfo, XMLElement, StreamInlet

KNOWN_ARRAY_ELEMENTS = ['channels']


def parse_to_dict(e: XMLElement, depth=0) -> Union[Dict[str, Any], List[Any], str]:
  # terminal case(s)
  if e.empty():
    return {}
  if e.is_text():
    return e.value()
  if e.first_child().is_text():
    return e.first_child().value()
  # check whether parsing a known array element
  d = [] if e.name() in KNOWN_ARRAY_ELEMENTS else {}
  # parse all children
  child = e.first_child()
  while not child.empty():
    p = parse_to_dict(child, depth + 1)
    if isinstance(d, dict):
      d[child.name()] = p
    elif isinstance(d, list):
      d.append(p)
    child = child.next_sibling()
  return d


def stream_info_to_dict(x: StreamInfo):
  temp_inlet = StreamInlet(x)
  desc = temp_inlet.info().desc()
  result = {
    'id': x.source_id(),
    'channel_count': x.channel_count(),
    'name': x.name(),
    'type': x.type(),
    **parse_to_dict(desc)
  }
  temp_inlet.close_stream()
  return result
