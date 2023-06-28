from __future__ import annotations

import itertools
from collections import OrderedDict
from typing import List, Optional

import numpy as np
import pydantic as p


class Field(p.BaseModel):
    name: str
    description: str
    dtype: type = p.Field(exclude=True)

    @p.validator("dtype", pre=True)
    def cast_to_type(cls, v):
        __map = {
            "f16": np.float16,
            "f32": np.float32,
            "f64": np.float64,
            "i8": np.int8,
            "i16": np.int16,
            "i32": np.int32,
            "u8": np.uint8,
            "u16": np.uint16,
            "u32": np.uint32,
        }
        return __map[v]


class Device(p.BaseModel):
    model: str
    manufacturer: str
    category: str


class Stream(p.BaseModel):
    name: str
    description: str
    unit: str
    frequency: float
    fields: OrderedDict[str, Field]
    index: OrderedDict[str, Field]
    node: Optional[Node] = p.Field(alias="@node")
    attrs: OrderedDict[str, str] = p.Field(default={})


class Node(p.BaseModel):
    device: Optional[Device]
    uri: Optional[str]
    inputs: OrderedDict[str, Stream] = p.Field(default={})
    outputs: OrderedDict[str, Stream] = p.Field(default={})


Stream.update_forward_refs()


class Author(p.BaseModel):
    name: str
    affiliation: str
    email: str


class Group(p.BaseModel):
    description: str
    values: List[str]


class Collection(p.BaseModel):
    name: str
    description: str
    keywords: List[str]
    authors: List[Author]
    streams: OrderedDict[str, Stream]
    groups: OrderedDict[str, Group]
    dataloader: str

    def iterate_groups(self):
        G = {k : v.values for k, v in self.groups.items()}
        K = list(G.keys())
        V = list(G.values())
        group_iter = itertools.product(*V)
        make_dict = lambda x: OrderedDict(zip(K, x))
        odict_iter = map(make_dict, group_iter)
        return list(odict_iter)
