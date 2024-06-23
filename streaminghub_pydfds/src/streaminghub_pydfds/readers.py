import abc
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from .const import dtype_map_inv


class FileReader(abc.ABC):

    @abc.abstractmethod
    def lsinfo(self) -> dict[str, dict[str, str]]:
        """
        List all data units within the file

        Returns:
            dict[str, dict[str, str]]: all data units and their attributes (optional)

        """

    @abc.abstractmethod
    def lsfields(self) -> dict[str, dict[str, str]]:
        """
        List fields of all data units within the file

        Returns:
            dict[str, dict[str, str]]: fields of all data units

        """

    @abc.abstractmethod
    def read(self, rec_path: str) -> tuple[dict, pd.DataFrame]:
        """
        Read metadata and data of a single unit.

        Returns:
            tuple[dict, pd.DataFrame]: (meta, data) tuple
        """


class HDF5Reader(FileReader):

    def __init__(self, fp: Path) -> None:
        assert fp.suffix in [".h5", ".hdf5"]
        self.fp = fp

    def lsinfo(self) -> dict[str, dict[str, str]]:
        files: dict[str, dict[str, str]] = {}
        with h5py.File(self.fp, "r") as file:
            for key, dataset in file.items():
                if not isinstance(dataset, h5py.Dataset):
                    continue
                files[key] = dict(dataset.attrs.items())
        return files

    def lsfields(self) -> dict[str, dict[str, str]]:
        attrs: dict[str, dict[str, str]] = {}
        with h5py.File(self.fp, "r") as file:
            for key, data in file.items():
                if not isinstance(data, h5py.Dataset):
                    continue
                attr: dict[str, str] = dict(data.dtype.descr)
                attrs[key] = attr
        return attrs

    def read(self, rec_path: str) -> tuple[dict, pd.DataFrame]:
        with h5py.File(self.fp, "r") as file:
            data = file.get(rec_path, default=None)  # type: ignore
            assert isinstance(data, h5py.Dataset)
            meta = dict(data.attrs.items())
            data = pd.DataFrame(np.array(data))
        return meta, data


class CSVReader(FileReader):

    def __init__(self, fp: Path) -> None:
        assert fp.suffix == ".csv"
        self.fp = fp

    def lsinfo(self) -> dict[str, dict[str, str]]:
        return {"root": {}}

    def lsfields(self) -> dict[str, dict[str, str]]:
        attrs: dict[str, dict[str, str]] = {}
        df = pd.read_csv(self.fp)
        attrs["root"] = df.dtypes.map(dtype_map_inv.__getitem__).to_dict()
        return attrs

    def read(self, rec_path: str) -> tuple[dict, pd.DataFrame]:
        # ignore rec_path
        data = pd.read_csv(self.fp)
        meta: dict[str, str] = {}  # TODO get extra metadata from elsewhere
        return meta, data


class ParquetReader(FileReader):

    def __init__(self, fp: Path) -> None:
        assert fp.suffix == ".parquet"
        self.fp = fp

    def lsinfo(self) -> dict[str, dict[str, str]]:
        return {"root": {}}

    def lsfields(self) -> dict[str, dict[str, str]]:
        attrs: dict[str, dict[str, str]] = {}
        df = pd.read_parquet(self.fp)
        attrs["root"] = df.dtypes.map(dtype_map_inv.__getitem__).to_dict()
        return attrs

    def read(self, rec_path: str) -> tuple[dict, pd.DataFrame]:
        # ignore rec_path
        data = pd.read_parquet(self.fp)
        meta: dict[str, str] = {}  # TODO get extra metadata from elsewhere
        return meta, data


def create_reader(fp: Path) -> FileReader:
    assert fp.suffix in [".h5", ".hdf5", ".parquet", ".csv"]
    if fp.suffix in [".h5", ".hdf5"]:
        return HDF5Reader(fp)
    elif fp.suffix == ".parquet":
        return ParquetReader(fp)
    elif fp.suffix == ".csv":
        return CSVReader(fp)
    else:
        raise ValueError(fp.suffix)
