from typing import Any, Dict, List

from .author import Author
from .group import Group
from .stream import Stream


class Collection:
    name: str
    description: str
    keywords: List[str]
    authors: List[Author]
    streams: Dict[str, Stream]
    groups: Dict[str, Group]
    resolver: str

    def __init__(
        self,
        name: str,
        description: str,
        keywords: List[str],
        authors: List[Author],
        streams: Dict[str, Stream],
        groups: Dict[str, Group],
        resolver: str,
    ) -> None:
        self.name = name
        self.description = description
        self.keywords = keywords
        self.authors = authors
        self.streams = streams
        self.groups = groups
        self.resolver = resolver

    @staticmethod
    def create(data: Dict[str, Any]):
        return Collection(
            name=str(data["name"]),
            description=str(data["description"]),
            keywords=[*map(str, data["keywords"])],
            authors=[*map(Author.create, data["authors"])],
            streams={k: Stream.create(v) for k, v in dict.items(data["streams"])},
            groups={k: Group.create(v) for k, v in dict.items(data["groups"])},
            resolver=str(data["resolver"]),
        )
