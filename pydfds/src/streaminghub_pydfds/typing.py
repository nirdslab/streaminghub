from __future__ import annotations

import itertools
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import parse
import pydantic as p

from .const import dtype_map_fwd, dtype_map_inv
from .readers import create_reader


class Config(p.BaseModel):
    data_dir: Path
    meta_dir: Path

    @p.field_validator("data_dir", "meta_dir", mode="before")
    def parse_path(cls, v) -> Path:
        path = Path(v).expanduser().resolve()
        assert path.exists() and path.is_dir()
        return path


class Field(p.BaseModel):
    name: str
    description: str
    dtype: type

    @p.field_validator("dtype", mode="before")
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
    id: str = p.Field(default="")
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
        config: Config,
    ) -> DataLoader:
        return DataLoader(self, config)


class DataLoader:
    """
    Provides functionality to list items and read data from DFDS collections.

    """

    def __init__(
        self,
        collection: Collection,
        config: Config,
    ) -> None:
        super().__init__()
        self.__collection = collection
        self.__protocol, self.__pattern = self.__collection.pattern.split("://", 1)
        self.__parser = parse.compile(self.__pattern)
        self.__fpath = Path(config.data_dir) / self.__collection.name

    def ls(
        self,
    ) -> List[dict[str, str]]:
        """
        Return the attributes of each record in the dataset

        Returns:
            List[dict[str, str]]: attributes of each record

        """
        available = []
        if self.__protocol == "h5":
            fp = self.__fpath / "data.h5"
            assert fp.exists() and fp.is_file()
            for key, attrs in create_reader(fp).lsinfo().items():
                result = self.__parser.parse(key)
                assert isinstance(result, parse.Result)
                available.append(attrs)
        elif self.__protocol == "parquet":
            fp = self.__fpath
            for key in fp.glob("*.parquet"):
                result = self.__parser.parse(key.with_suffix("").name)
                assert isinstance(result, parse.Result)
                available.append({})
        elif self.__protocol == "csv":
            fp = self.__fpath
            for key in fp.glob("*.csv"):
                result = self.__parser.parse(key.with_suffix("").name)
                assert isinstance(result, parse.Result)
                available.append({})
        else:
            raise ValueError(f"Unsupported protocol: {self.__protocol}")

        # patch metadata with collection / path information
        for attrs in available:
            attrs.update({"collection": self.__collection.name, **result.named})

        return available

    def read(
        self,
        attributes: dict,
    ) -> Tuple[dict, pd.DataFrame]:
        """
        Given the attributes of a record, return its data

        Args:
            attributes (dict): attributes of the requested record

        Returns:
            Tuple[dict, pd.DataFrame]: (attributes, data) of the requested record
        """
        # compute the path from attributes
        parser_keys: List[str] = self.__parser.named_fields
        parser_attrs = {k: v for k, v in attributes.items() if k in parser_keys}
        rec_path = str.format(self.__parser._format, **parser_attrs)

        # Derive the file path
        if self.__protocol == "h5":
            fp = self.__fpath / "data.h5"
        elif self.__protocol == "parquet":
            fp = self.__fpath / (rec_path + ".parquet")
        elif self.__protocol == "csv":
            fp = self.__fpath / (rec_path + ".csv")
        else:
            raise ValueError(f"Unsupported protocol: {self.__protocol}")

        # load meta and data from file path
        assert fp.exists() and fp.is_file()
        meta, data = create_reader(fp).read(rec_path)

        # patch metadata with collection / path information
        meta.update({"collection": self.__collection.name, **parser_attrs})

        return meta, data
