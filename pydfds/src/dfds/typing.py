from __future__ import annotations

import itertools
from typing import List, Optional, Tuple

import h5py
import numpy as np
import parse
import pydantic as p

dtype_map_fwd = {
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

dtype_map_inv = {
    np.float16: "f16",
    np.float32: "f32",
    np.float64: "f64",
    np.int8: "i8",
    np.int16: "i16",
    np.int32: "i32",
    np.uint8: "u8",
    np.uint16: "u16",
    np.uint32: "u32",
}


class Field(p.BaseModel):
    name: str
    description: str
    dtype: type

    @p.field_validator("dtype", mode='before')
    def parse_dtype(cls, v):
        return dtype_map_fwd[v]

    @p.field_serializer("dtype")
    def serialize_dtype(self, v, i):
        return dtype_map_inv[v]


class Device(p.BaseModel):
    model: str
    manufacturer: str
    category: str


class Stream(p.BaseModel):
    name: str
    description: str
    unit: str
    frequency: float
    fields: dict[str, Field]
    index: dict[str, Field]
    node: Optional[Node] = p.Field(alias="@node", default=None)
    attrs: dict[str, str] = p.Field(default=dict())


class Node(p.BaseModel):
    device: Optional[Device] = p.Field(default=None)
    uri: Optional[str] = p.Field(default=None)
    inputs: dict[str, Stream] = p.Field(default=dict())
    outputs: dict[str, Stream] = p.Field(default=dict())


Stream.model_rebuild()


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
    streams: dict[str, Stream]
    groups: dict[str, Group]
    pattern: str

    def iterate_groups(self):
        G = {k: v.values for k, v in self.groups.items()}
        K = list(G.keys())
        V = list(G.values())
        group_iter = itertools.product(*V)
        make_dict = lambda x: dict(zip(K, x))
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

        import os
        base_dir = os.getenv("SHUB_DATA_DIR")
        assert base_dir
        self.__fpath = os.path.join(base_dir, self.__collection.name, "data.h5")
        assert os.path.isfile(self.__fpath)

    def ls(
        self,
    ) -> List[dict[str, str]]:
        """
        Return the attributes of each record in the dataset

        Returns:
            List[dict[str, str]]: attributes of each record

        """
        available = []
        with h5py.File(self.__fpath, "r") as file:
            for key, dataset in file.items():
                if not isinstance(dataset, h5py.Dataset):
                    continue
                result = self.__parser.parse(key)
                assert isinstance(result, parse.Result)
                attrs: dict[str, str] = dict(dataset.attrs.items())
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
        parser_keys: List[str] = self.__parser.named_fields
        parser_attrs = {k: v for k, v in attributes.items() if k in parser_keys}
        rec_path = str.format(self.__parser._format, **parser_attrs)
        # Read the record from file
        with h5py.File(self.__fpath, "r") as file:
            dataset = file.get(rec_path, default=None)  # type: ignore
            assert isinstance(dataset, h5py.Dataset)
            attrs = dict(dataset.attrs.items())
            attrs.update({"collection": self.__collection.name, **parser_attrs})
            data = np.array(dataset)
        return attrs, data
