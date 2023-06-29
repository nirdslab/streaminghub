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

    def dataloader(
        self,
    ) -> DataLoader:
        return DataLoader(self)


class DataLoader:
    """
    Provides functionality to list items and read data from DFDS collections.

    """

    def __init__(
        self,
        collection: Collection,
    ) -> None:
        super().__init__()
        self.__collection = collection
        self.__parser = parse.compile(self.__collection.pattern)
        base_dir = os.getenv("DATA_DIR")
        assert base_dir
        self.__fpath = os.path.join(base_dir, self.__collection.name, "data.h5")
        assert os.path.isfile(self.__fpath)

    def ls(
        self,
    ) -> List[dict]:
        """
        Return the attributes of each record in the dataset

        Returns:
            List[dict]: attributes of each record

        """
        available = []
        with h5py.File(self.__fpath, "r") as file:
            for key, dataset in file.items():
                if not isinstance(dataset, h5py.Dataset):
                    continue
                result = self.__parser.parse(key)
                assert isinstance(result, parse.Result)
                attrs = dict(dataset.attrs.items())
                attrs.update({"collection": self.__collection.name, **result.named})
                available.append(attrs)
        return available

    def read(
        self,
        attributes: dict,
    ) -> Tuple[dict, np.ndarray]:
        """
        Given the attributes of a record, return its data

        Args:
            attributes (dict): attributes of the requested record

        Returns:
            Tuple[dict, np.ndarray]: (attributes, data) of the requested record
        """
        # compute the path from attributes
        safe_keys: List[str] = self.__parser.named_fields
        safe_attributes = {k: attributes[k] for k in safe_keys}
        rec_path = str.format(self.__parser._format, safe_attributes)
        # Read the record from file
        with h5py.File(self.__fpath, "r") as file:
            dataset = file.get(rec_path, default=None)  # type: ignore
            assert isinstance(dataset, h5py.Dataset)
            attrs = dict(dataset.attrs.items())
            attrs.update({"dataset": self.__collection.name, **safe_attributes})
            data = np.array(dataset)
        return attrs, data
