import pylsl
import xmltodict
from streaminghub_pydfds.typing import Stream


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
