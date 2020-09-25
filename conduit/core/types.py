from typing import List


class MetaStream(dict):
    """
    Meta-stream object
    """

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = self.Info(d['info'])
            self.device = self.DeviceInfo(d['device'])
            self.fields = [self.FieldInfo(field) for field in d['fields']]
            self.streams = [self.StreamInfo(stream) for stream in d['streams']]

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
            self['frequency'] = float(value)

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

    def __init__(self, d=None) -> None:
        super().__init__()
        if d is not None:
            self.info = self.Info(d['info'])
            self.dataset = self.DatasetInfo(d['dataset'])
            self.fields = [self.FieldInfo(field) for field in d['fields']]
            self.links = [self.LinkInfo(field) for field in d['links']]
            self.sources = self.SourceInfo(d['sources'])

    class Info(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.version = d['version']
                self.created = d['created']
                self.modified = d['modified']
                self.checksum = d['checksum']

        @property
        def version(self) -> str:
            return self['version']

        @version.setter
        def version(self, value: str):
            self['version'] = value

        @property
        def created(self) -> str:
            return self['created']

        @created.setter
        def created(self, value: str):
            self['created'] = value

        @property
        def modified(self) -> str:
            return self['modified']

        @modified.setter
        def modified(self, value: str):
            self['modified'] = value

        @property
        def checksum(self) -> str:
            return self['checksum']

        @checksum.setter
        def checksum(self, value: str):
            self['checksum'] = value

    class DatasetInfo(dict):

        class AuthorInfo(dict):
            def __init__(self, d=None) -> None:
                super().__init__()
                if d is not None:
                    self.name = d['name']
                    self.affiliation = d['affiliation']
                    self.email = d['email']

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

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.name = d['name']
                self.description = d['description']
                self.keywords = [str(keyword) for keyword in d['keywords']]
                self.authors = [self.AuthorInfo(author) for author in d['authors']]

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

    class LinkInfo(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.type = d['type']
                self.fields = [str(field) for field in d['fields']]

        @property
        def type(self) -> str:
            return self['type']

        @type.setter
        def type(self, value: str):
            self['type'] = value

        @property
        def fields(self) -> List[str]:
            return self['fields']

        @fields.setter
        def fields(self, value: List[str]):
            self['fields'] = value

    class SourceInfo(dict):

        def __init__(self, d=None) -> None:
            super().__init__()
            if d is not None:
                self.meta_streams = [self.MetaStreamInfo(field) for field in d['meta-streams']]
                self.files = [self.FileInfo(field) for field in d['files']]

        class MetaStreamInfo(dict):

            def __init__(self, d=None) -> None:
                super().__init__()
                if d is not None:
                    self.device = MetaStream.DeviceInfo(d['device'])
                    self.streams = [MetaStream.StreamInfo(field) for field in d['streams']]

            @property
            def device(self) -> MetaStream.DeviceInfo:
                return self['device']

            @device.setter
            def device(self, value: MetaStream.DeviceInfo):
                self['device'] = value

            @property
            def streams(self) -> List[MetaStream.StreamInfo]:
                return self['streams']

            @streams.setter
            def streams(self, value: List[MetaStream.StreamInfo]):
                self['streams'] = value

        class FileInfo(dict):

            def __init__(self, d=None) -> None:
                super().__init__()
                if d is not None:
                    self.checksum = d['checksum']
                    self.path = d['path']
                    self.encoding = d['encoding']
                    self.description = d['description']
                    self.keys = [str(field) for field in d['keys']]

            @property
            def checksum(self) -> str:
                return self['checksum']

            @checksum.setter
            def checksum(self, value: str):
                self['checksum'] = value

            @property
            def path(self) -> str:
                return self['path']

            @path.setter
            def path(self, value: str):
                self['path'] = value

            @property
            def encoding(self) -> str:
                return self['encoding']

            @encoding.setter
            def encoding(self, value: str):
                self['encoding'] = value

            @property
            def description(self) -> str:
                return self['description']

            @description.setter
            def description(self, value: str):
                self['description'] = value

            @property
            def keys(self) -> List[str]:
                return self['keys']

            @keys.setter
            def keys(self, value: List[str]):
                self['keys'] = value

        @property
        def meta_streams(self) -> List[MetaStreamInfo]:
            return self['meta_streams']

        @meta_streams.setter
        def meta_streams(self, value: List[MetaStreamInfo]):
            self['meta_streams'] = value

        @property
        def files(self) -> List[FileInfo]:
            return self['files']

        @files.setter
        def files(self, value: List[FileInfo]):
            self['files'] = value

    @property
    def info(self) -> Info:
        return self['info']

    @info.setter
    def info(self, value: Info):
        self['info'] = value

    @property
    def dataset(self) -> DatasetInfo:
        return self['dataset']

    @dataset.setter
    def dataset(self, value: DatasetInfo):
        self['dataset'] = value

    @property
    def fields(self) -> List[FieldInfo]:
        return self['fields']

    @fields.setter
    def fields(self, value: List[FieldInfo]):
        self['fields'] = value

    @property
    def links(self) -> List[LinkInfo]:
        return self['links']

    @links.setter
    def links(self, value: List[LinkInfo]):
        self['links'] = value

    @property
    def sources(self) -> SourceInfo:
        return self['sources']

    @sources.setter
    def sources(self, value: SourceInfo):
        self['sources'] = value


class AnalyticStream(dict):
    """
    Analytic-stream object
    """
    pass
