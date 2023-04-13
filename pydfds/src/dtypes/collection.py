from typing import Any, Dict, List, Union

from .author import Author
from .group import Group
from .pipe import Pipe
from .stream import Stream
from .util import stream_or_pipe


class Collection:
    
    name: str
    description: str
    keywords: List[str]
    authors: List[Author]
    streams: Dict[str, Union[Pipe, Stream]]
    groups: Dict[str, Group]
    dataloader: str

    def __init__(
        self,
        name: str,
        description: str,
        keywords: List[str],
        authors: List[Author],
        streams: Dict[str, Union[Pipe, Stream]],
        groups: Dict[str, Group],
        dataloader: str,
    ) -> None:
        self.name = name
        self.description = description
        self.keywords = keywords
        self.authors = authors
        self.streams = streams
        self.groups = groups
        self.dataloader = dataloader

    @staticmethod
    def create(data: Dict[str, Any]):
        streams = {}
        return Collection(
            name=str(data["name"]),
            description=str(data["description"]),
            keywords=[*map(str, data["keywords"])],
            authors=[*map(Author.create, data["authors"])],
            streams={k: stream_or_pipe(v) for k, v in dict.items(data["streams"])},
            groups={k: Group.create(v) for k, v in dict.items(data["groups"])},
            dataloader=str(data["dataloader"]),
        )
