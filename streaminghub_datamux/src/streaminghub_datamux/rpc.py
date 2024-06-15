import asyncio
import logging
from abc import ABC, abstractmethod
from functools import singledispatch
from importlib.metadata import entry_points
from typing import Any

import numpy as np


@singledispatch
def to_serializable(val: Any) -> Any:
    """Used by default."""
    return str(val)


@to_serializable.register(np.float32)
def ts_float32(val: np.float32):
    """Used if *val* is an instance of numpy.float32."""
    return np.float64(val)


class RpcClient(ABC):
    """
    Base Class for RPC Client

    """

    @abstractmethod
    def __init__(
        self,
        codec_name: str,
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None: ...

    @abstractmethod
    async def connect(self, server_host: str, server_port: int) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...


class RpcCodec(ABC):
    """
    Base Class for RPC Codec

    """

    def __init__(
        self,
    ):
        self.logger = logging.getLogger(__name__)
        self.active = False

    @abstractmethod
    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes | list[bytes]: ...

    @abstractmethod
    def decode(
        self,
        payload: bytes,
    ) -> tuple[bytes, dict] | None: ...


class RpcServer(ABC):
    """
    Base Class for RPC Server

    """

    @abstractmethod
    def __init__(
        self,
        codecs: dict[str, type[RpcCodec]],
        incoming: asyncio.Queue,
        outgoing: asyncio.Queue,
    ) -> None: ...

    @abstractmethod
    async def start(self, host: str, port: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...


def create_rpc_client(
    name: str,
    codec_name: str,
    incoming: asyncio.Queue,
    outgoing: asyncio.Queue,
) -> RpcClient:
    try:
        klass = entry_points(name=name, group="streaminghub_datamux.rpc.client").pop().load()
    except:
        raise ValueError(f"Unkown streaminghub_datamux.rpc.client:{name}")
    if issubclass(klass, RpcClient):
        print(f"Loaded streaminghub_datamux.rpc.client:{name}")
        return klass(codec_name, incoming, outgoing)
    else:
        raise ValueError(f"Invalid streaminghub_datamux.rpc.client:{name}")


def create_rpc_server(
    name: str,
    incoming: asyncio.Queue,
    outgoing: asyncio.Queue,
) -> RpcServer:
    codecs = get_rpc_codecs()
    try:
        klass = entry_points(name=name, group="streaminghub_datamux.rpc.server").pop().load()
    except:
        raise ValueError(f"Unkown streaminghub_datamux.rpc.server:{name}")
    if issubclass(klass, RpcServer):
        print(f"Loaded streaminghub_datamux.rpc.server:{name}")
        return klass(codecs, incoming, outgoing)
    else:
        raise ValueError(f"Invalid streaminghub_datamux.rpc.server:{name}")


def get_rpc_codecs() -> dict[str, type[RpcCodec]]:
    codecs = {}
    for ep in entry_points(group="streaminghub_datamux.rpc.codec"):
        klass = ep.load()
        if issubclass(klass, RpcCodec):
            print(f"Loaded streaminghub_datamux.rpc.codec:{ep.name}")
            codecs[ep.name] = klass
        else:
            print(f"Invalid streaminghub_datamux.rpc.codec:{ep.name}")
    return codecs


def create_rpc_codec(
    name: str,
) -> RpcCodec:
    try:
        klass = entry_points(name=name, group="streaminghub_datamux.rpc.codec").pop().load()
    except:
        raise ValueError(f"Unkown streaminghub_datamux.rpc.codec:{name}")
    if issubclass(klass, RpcCodec):
        print(f"Loaded streaminghub_datamux.rpc.codec:{name}")
        return klass()
    else:
        raise ValueError(f"Invalid streaminghub_datamux.rpc.codec:{name}")
