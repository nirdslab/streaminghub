import asyncio
from importlib.metadata import entry_points

from .client import RpcClient
from .codec import RpcCodec
from .server import RpcServer
from .util import to_serializable


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
