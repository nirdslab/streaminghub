from lxml import etree

from core.types import MetaStream, MetaFile, AnalyticStream


def __parse_etree_into_meta_stream(data: etree) -> MetaStream:
    spec = MetaStream()
    root = data.getroot().xpath('/meta-stream')[0]
    # parse info
    spec.info = MetaStream.Info()
    spec.info.version = root.xpath('info/version')[0].text
    spec.info.checksum = root.xpath('info/checksum')[0].text
    # parse device info
    spec.device = MetaStream.DeviceInfo()
    spec.device.model = root.xpath('device/model')[0].text
    spec.device.manufacturer = root.xpath('device/manufacturer')[0].text
    spec.device.category = root.xpath('device/category')[0].text
    # parse fields
    spec.fields = []
    for field in root.xpath('fields/field'):
        field_info = MetaStream.FieldInfo()
        field_info.id = field.xpath('id')[0].text
        field_info.name = field.xpath('name')[0].text
        field_info.description = field.xpath('description')[0].text
        field_info.dtype = field.xpath('dtype')[0].text
        spec.fields.append(field_info)
    # parse streams
    spec.streams = []
    for stream in root.xpath('streams/stream'):
        stream_info = MetaStream.StreamInfo()
        stream_info.name = stream.xpath('name')[0].text
        stream_info.description = stream.xpath('description')[0].text
        stream_info.unit = stream.xpath('unit')[0].text
        stream_info.frequency = stream.xpath('frequency')[0].text
        stream_info.channels = [x.text for x in stream.xpath('channels/channel')]
        spec.streams.append(stream_info)
    return spec


def __parse_etree_into_meta_file(data: etree) -> MetaFile:
    meta = MetaFile()
    return meta


def __parse_etree_into_analytic_stream(data: etree) -> AnalyticStream:
    meta = AnalyticStream()
    return meta


def __parse_dict_into_meta_stream(data: dict) -> MetaStream:
    meta = MetaStream(data)
    return meta


def __parse_dict_into_meta_file(data: dict) -> MetaFile:
    meta = MetaFile()
    return meta


def __parse_dict_into_analytic_stream(data: dict) -> AnalyticStream:
    meta = AnalyticStream()
    return meta
