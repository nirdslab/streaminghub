from typing import Dict, List

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
    dataloader: str

    def __init__(
        self,
        name: str,
        description: str,
        keywords: List[str],
        authors: List[Author],
        streams: Dict[str, Stream],
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
