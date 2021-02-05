from lxml import etree

from core.types import Datasource, Dataset, Analytic


def __parse_etree_into_meta_stream(data: etree) -> Datasource:
    spec = Datasource()
    root = data.getroot().xpath('/meta-stream')[0]
    # parse info
    spec.info = Datasource.Info()
    spec.info.version = root.xpath('info/version')[0].text
    spec.info.checksum = root.xpath('info/checksum')[0].text
    # parse device info
    spec.device = Datasource.DeviceInfo()
    spec.device.model = root.xpath('device/model')[0].text
    spec.device.manufacturer = root.xpath('device/manufacturer')[0].text
    spec.device.category = root.xpath('device/category')[0].text
    # parse fields
    spec.fields = []
    for field in root.xpath('fields/field'):
        field_info = Datasource.FieldInfo()
        field_info.id = field.xpath('id')[0].text
        field_info.name = field.xpath('name')[0].text
        field_info.description = field.xpath('description')[0].text
        field_info.dtype = field.xpath('dtype')[0].text
        spec.fields.append(field_info)
    # parse streams
    spec.streams = []
    for stream in root.xpath('streams/stream'):
        stream_info = Datasource.StreamInfo()
        stream_info.name = stream.xpath('name')[0].text
        stream_info.description = stream.xpath('description')[0].text
        stream_info.unit = stream.xpath('unit')[0].text
        if stream_info.unit is None:
            stream_info.unit = ""
        stream_info.frequency = stream.xpath('frequency')[0].text
        stream_info.channels = [x.text for x in stream.xpath('channels/channel')]
        spec.streams.append(stream_info)
    return spec


def __parse_etree_into_meta_file(data: etree) -> Dataset:
    meta = Dataset()
    return meta


def __parse_etree_into_analytic_stream(data: etree) -> Analytic:
    meta = Analytic()
    return meta


def __parse_dict_into_meta_stream(data: dict) -> Datasource:
    return Datasource(d=data)


def __parse_dict_into_meta_file(data: dict) -> Dataset:
    return Dataset(d=data)


def __parse_dict_into_analytic_stream(data: dict) -> Analytic:
    meta = Analytic()
    return meta
