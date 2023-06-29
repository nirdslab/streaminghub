from __future__ import annotations

import itertools
import os
from collections import OrderedDict
from typing import List, Optional, Tuple

import h5py
import numpy as np
import parse
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
    pattern: str

    def iterate_groups(self):
        G = {k: v.values for k, v in self.groups.items()}
        K = list(G.keys())
        V = list(G.values())
        group_iter = itertools.product(*V)
        make_dict = lambda x: OrderedDict(zip(K, x))
        odict_iter = map(make_dict, group_iter)
        return list(odict_iter)


class DataLoader:
    def __init__(
        self,
        spec: Collection,
    ) -> None:
        super().__init__()
        self.spec = spec
        self.parser = parse.compile(self.spec.pattern)
        base_dir = os.getenv("DATA_DIR")
        assert base_dir
        dataset_path = os.path.join(base_dir, self.spec.name, "data.h5")
        assert os.path.isfile(dataset_path)
        self.dataset_path = dataset_path

    def fetch(
        self,
        params: dict,
    ) -> Tuple[dict, np.ndarray]:
        query = self.generate_query(params)
        attrs, data = self.execute_query(query)
        return attrs, data

    def list_available(
        self,
    ) -> List[dict]:
        available = []
        with h5py.File(self.dataset_path, "r") as file:
            for key, dataset in file.items():
                if not isinstance(dataset, h5py.Dataset):
                    continue
                result = self.parser.parse(key)
                assert isinstance(result, parse.Result)
                attrs = dict(dataset.attrs.items())
                attrs.update({"dataset": self.spec.name, **result.named})
                available.append(attrs)
        return available

    def generate_query(
        self,
        params: dict,
    ) -> dict:
        allowed_params: List[str] = self.parser.named_fields
        query = {k: params[k] for k in allowed_params}
        return query

    def execute_query(
        self,
        query: dict,
    ) -> Tuple[dict, np.ndarray]:
        with h5py.File(self.dataset_path, "r") as file:
            data_path = str.format(self.parser._format, query)
            dataset = file.get(data_path, default=None)  # type: ignore
            assert isinstance(dataset, h5py.Dataset)
            attrs = dict(dataset.attrs.items())
            attrs.update({"dataset": self.spec.name, **query})
            data = np.array(dataset)
        return attrs, data
