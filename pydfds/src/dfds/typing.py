from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Field(BaseModel):
    name: str
    description: str
    dtype: type


class Stream(BaseModel):
    name: str
    description: str
    unit: str
    frequency: float
    fields: Dict[str, Field]
    index: Dict[str, Field]
    node: Any


class Device(BaseModel):
    model: str
    manufacturer: str
    category: str


class Node(BaseModel):
    device: Optional[Device]
    uri: Optional[str]
    inputs: Dict[str, Stream]
    outputs: Dict[str, Stream]


class Author(BaseModel):
    name: str
    affiliation: str
    email: str


class Group(BaseModel):
    description: str
    values: List[str]


class Collection(BaseModel):
    name: str
    description: str
    keywords: List[str]
    authors: List[Author]
    streams: Dict[str, Stream]
    groups: Dict[str, Group]
    dataloader: str
