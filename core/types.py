from typing import List


class MetaStream(dict):
    """
    Meta-stream object
    """

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = MetaStream.Info(d['info'])
            self.device = MetaStream.DeviceInfo(d['device'])
            self.fields = [MetaStream.FieldInfo(field) for field in d['fields']]
            self.streams = [MetaStream.StreamInfo(stream) for stream in d['streams']]

    class Info(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.version = d['version']
                self.checksum = d['checksum']

        @property
        def version(self) -> str:
            return self['version']

        @version.setter
        def version(self, value: str):
            self['version'] = value

        @property
        def checksum(self) -> str:
            return self['checksum']

        @checksum.setter
        def checksum(self, value: str):
            self['checksum'] = value

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

    class FieldInfo(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.id = d['id']
                self.name = d['name']
                self.description = d['description']
                self.dtype = d['dtype']

        @property
        def id(self) -> str:
            return self['id']

        @id.setter
        def id(self, value: str):
            self['id'] = value

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

    class StreamInfo(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.name = d['name']
                self.description = d['description']
                self.unit = d['unit']
                self.frequency = d['frequency']
                self.channels = d['channels']

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
            self['frequency'] = value

        @property
        def channels(self) -> List[str]:
            return self['channels']

        @channels.setter
        def channels(self, value: List[str]):
            self['channels'] = value

    @property
    def info(self) -> Info:
        return self['info']

    @info.setter
    def info(self, value: Info):
        self['info'] = value

    @property
    def device(self) -> DeviceInfo:
        return self['device']

    @device.setter
    def device(self, value: DeviceInfo):
        self['device'] = value

    @property
    def fields(self) -> List[FieldInfo]:
        return self['fields']

    @fields.setter
    def fields(self, value: List[FieldInfo]):
        self['fields'] = value

    @property
    def streams(self) -> List[StreamInfo]:
        return self['streams']

    @streams.setter
    def streams(self, value: List[StreamInfo]):
        self['streams'] = value


class MetaFile(dict):
    """
    Meta-file object
    """
    pass


class AnalyticStream(dict):
    """
    Analytic-stream object
    """
    pass
