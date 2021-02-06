from typing import List, Dict


class FieldInfo(dict):

    def __init__(self, _d=None) -> None:
        super().__init__()
        if _d is not None:
            self.name = _d['name']
            self.description = _d['description']
            self.dtype = _d['dtype']

    @property
    def name(self) -> str:
        return self['name']

    @name.setter
    def name(self, value: str):
        self['name'] = value

    @property
    def description(self) -> str:
        return self['description']

    @description.setter
    def description(self, value: str):
        self['description'] = value

    @property
    def dtype(self) -> str:
        return self['dtype']

    @dtype.setter
    def dtype(self, value: str):
        self['dtype'] = value


class IdInfo(dict):

    def __init__(self, _d=None) -> None:
        super().__init__()
        if _d is not None:
            self.version = _d['version']
            self.timestamp = _d['timestamp']
            self.checksum = _d['checksum']

    @property
    def version(self) -> str:
        return self['version']

    @version.setter
    def version(self, value: str):
        self['version'] = value

    @property
    def timestamp(self) -> str:
        return self['timestamp']

    @timestamp.setter
    def timestamp(self, value: str):
        self['timestamp'] = value

    @property
    def checksum(self) -> str:
        return self['checksum']

    @checksum.setter
    def checksum(self, value: str):
        self['checksum'] = value


class AuthorInfo(dict):
    def __init__(self, _d=None) -> None:
        super().__init__()
        if _d is not None:
            self.name = _d['name']
            self.affiliation = _d['affiliation']
            self.email = _d['email']

    @property
    def name(self) -> str:
        return self['name']

    @name.setter
    def name(self, value: str):
        self['name'] = value

    @property
    def affiliation(self) -> str:
        return self['affiliation']

    @affiliation.setter
    def affiliation(self, value: str):
        self['affiliation'] = value

    @property
    def email(self) -> str:
        return self['email']

    @email.setter
    def email(self, value: str):
        self['email'] = value


class GroupInfo(dict):

    def __init__(self, _d=None) -> None:
        super().__init__()
        if _d is not None:
            self.description = _d['description']
            self.attributes = _d['attributes']

    @property
    def description(self) -> str:
        return self['description']

    @description.setter
    def description(self, value: str):
        self['description'] = value

    @property
    def attributes(self) -> List[str]:
        return self['attributes']

    @attributes.setter
    def attributes(self, value: List[str]):
        self['attributes'] = value

    # ============================


class DeviceInfo(dict):

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.model = d['model']
            self.manufacturer = d['manufacturer']
            self.category = d['category']

    @property
    def model(self) -> str:
        return self['model']

    @model.setter
    def model(self, value: str):
        self['model'] = value

    @property
    def manufacturer(self) -> str:
        return self['manufacturer']

    @manufacturer.setter
    def manufacturer(self, value: str):
        self['manufacturer'] = value

    @property
    def category(self) -> str:
        return self['category']

    @category.setter
    def category(self, value: str):
        self['category'] = value


class StreamInfo(dict):

    def __init__(self, _d=None) -> None:
        super().__init__()
        if _d is not None:
            self.name = _d['name']
            self.description = _d['description']
            self.unit = _d['unit']
            self.frequency = _d['frequency']
            self.index = FieldInfo(_d['index'])
            self.channels = [FieldInfo(channel) for channel in _d['channels']]

    @property
    def name(self) -> str:
        return self['name']

    @name.setter
    def name(self, value: str):
        self['name'] = value

    @property
    def description(self) -> str:
        return self['description']

    @description.setter
    def description(self, value: str):
        self['description'] = value

    @property
    def unit(self) -> str:
        return self['unit']

    @unit.setter
    def unit(self, value: str):
        self['unit'] = value

    @property
    def frequency(self) -> float:
        return float(self['frequency'])

    @frequency.setter
    def frequency(self, value: float):
        self['frequency'] = float(value)

    @property
    def index(self) -> FieldInfo:
        return self['index']

    @index.setter
    def index(self, value: FieldInfo):
        self['index'] = value

    @property
    def channels(self) -> List[FieldInfo]:
        return self['channels']

    @channels.setter
    def channels(self, value: List[FieldInfo]):
        self['channels'] = value


# Schema Definition Classes
# ============================


class DataSourceSpec(dict):
    """
    DataSource object
    """

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = IdInfo(d['info'])
            self.device = DeviceInfo(d['device'])
            self.fields = {field: FieldInfo(d['fields'][field]) for field in d['fields']}
            self.streams = {stream: StreamInfo(d['streams'][stream]) for stream in d['streams']}

    @property
    def info(self) -> IdInfo:
        return self['info']

    @info.setter
    def info(self, value: IdInfo):
        self['info'] = value

    @property
    def device(self) -> DeviceInfo:
        return self['device']

    @device.setter
    def device(self, value: DeviceInfo):
        self['device'] = value

    @property
    def fields(self) -> Dict[str, FieldInfo]:
        return self['fields']

    @fields.setter
    def fields(self, value: Dict[str, FieldInfo]):
        self['fields'] = value

    @property
    def streams(self) -> Dict[str, StreamInfo]:
        return self['streams']

    @streams.setter
    def streams(self, value: Dict[str, StreamInfo]):
        self['streams'] = value


class DataSetSpec(dict):
    """
    Dataset object
    """

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = IdInfo(d['info'])
            self.name = d['name']
            self.description = d['description']
            self.keywords = d['keywords']
            self.authors = [AuthorInfo(author) for author in d['authors']]
            self.sources = {source: DataSourceSpec(d['sources'][source]) for source in d['sources']}
            self.fields = {field: FieldInfo(d['fields'][field]) for field in d['fields']}
            self.groups = {group: GroupInfo(d['groups'][group]) for group in d['groups']}

    @property
    def info(self) -> IdInfo:
        return self['info']

    @info.setter
    def info(self, value: IdInfo):
        self['info'] = value

    @property
    def name(self) -> str:
        return self['name']

    @name.setter
    def name(self, value: str):
        self['name'] = value

    @property
    def description(self) -> str:
        return self['description']

    @description.setter
    def description(self, value: str):
        self['description'] = value

    @property
    def keywords(self) -> List[str]:
        return self['keywords']

    @keywords.setter
    def keywords(self, value: List[str]):
        self['keywords'] = value

    @property
    def authors(self) -> List[AuthorInfo]:
        return self['authors']

    @authors.setter
    def authors(self, value: List[AuthorInfo]):
        self['authors'] = value

    @property
    def sources(self) -> Dict[str, DataSourceSpec]:
        return self['sources']

    @sources.setter
    def sources(self, value: Dict[str, DataSourceSpec]):
        self['sources'] = value

    @property
    def fields(self) -> Dict[str, FieldInfo]:
        return self['fields']

    @fields.setter
    def fields(self, value: Dict[str, FieldInfo]):
        self['fields'] = value

    @property
    def groups(self) -> Dict[str, GroupInfo]:
        return self['groups']

    @groups.setter
    def groups(self, value: Dict[str, GroupInfo]):
        self['groups'] = value


class AnalyticSpec(dict):
    """
    Analytic object
    """

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = IdInfo(d['info'])
            self.sources = {source: DataSourceSpec(d['sources'][source]) for source in d['sources']}
            self.fields = {field: FieldInfo(d['fields'][field]) for field in d['fields']}
            self.inputs = {input_stream: StreamInfo(d['inputs'][input_stream]) for input_stream in d['inputs']}
            self.streams = {stream: StreamInfo(d['streams'][stream]) for stream in d['streams']}

    @property
    def info(self) -> IdInfo:
        return self['info']

    @info.setter
    def info(self, value: IdInfo):
        self['info'] = value

    @property
    def sources(self) -> Dict[str, DataSourceSpec]:
        return self['sources']

    @sources.setter
    def sources(self, value: Dict[str, DataSourceSpec]):
        self['sources'] = value

    @property
    def fields(self) -> Dict[str, FieldInfo]:
        return self['fields']

    @fields.setter
    def fields(self, value: Dict[str, FieldInfo]):
        self['fields'] = value

    @property
    def inputs(self) -> Dict[str, StreamInfo]:
        return self['inputs']

    @inputs.setter
    def inputs(self, value: Dict[str, StreamInfo]):
        self['inputs'] = value

    @property
    def streams(self) -> Dict[str, StreamInfo]:
        return self['streams']

    @streams.setter
    def streams(self, value: Dict[str, StreamInfo]):
        self['streams'] = value
