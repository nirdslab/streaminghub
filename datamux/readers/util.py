from typing import Union, List, Any
from dfds.typing import Stream, Node
import pylsl


def create_stream_from_info(
    lsl_stream: pylsl.StreamInfo,
) -> Stream:
    # TODO if streams contain node metadata, read them.
    # TODO otherwise, fetch them from repository.
    # TODO update with correct stream metadata

    assert lsl_stream

    node_info = {}
    node = Node(**node_info)

    stream_info = {}
    stream = Stream(**{**stream_info, "@node": node})

    return stream


def gen_dict(
    e: pylsl.XMLElement,
    depth=0,
) -> Union[dict, List[Any], str]:
    # terminal case(s)
    if e.empty():
        return {}
    if e.is_text():
        return e.value()
    if e.first_child().is_text():
        return e.first_child().value()
    d = {}
    # parse all children
    child = e.first_child()
    while not child.empty():
        p = gen_dict(child, depth + 1)
        if isinstance(d, dict):
            d[child.name()] = p
        elif isinstance(d, list):
            d.append(p)
        child = child.next_sibling()
    return d


def gen_stream_info_dict(
    x: Union[pylsl.StreamInfo, pylsl.StreamInlet],
):
    def fn(i: pylsl.StreamInfo):
        p = gen_dict(i.desc())
        assert isinstance(p, dict)
        return {
            "source": i.source_id(),
            "mode": "live",
            **p,
        }

    if isinstance(x, pylsl.StreamInfo):
        temp_inlet = pylsl.StreamInlet(x)
        result = fn(temp_inlet.info())
        temp_inlet.close_stream()
    elif isinstance(x, pylsl.StreamInlet):
        result = fn(x.info())
    else:
        raise RuntimeError("Invalid object type")
    return result
