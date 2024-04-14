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
    for ep in entry_points(group="streaminghub_datamux.rpc.client"):
        if ep.name == name:
            client = ep.load()
            if issubclass(client, RpcClient):
                print(f"Loaded RPC client: {name}")
                return client(codec_name, incoming, outgoing)
            else:
                print(f"Invalid RPC client: {name}")
    raise ValueError(f"RPC client not found: {name}")


def create_rpc_server(
    name: str,
    codec_name: str,
    incoming: asyncio.Queue,
    outgoing: asyncio.Queue,
) -> RpcServer:
    for ep in entry_points(group="streaminghub_datamux.rpc.server"):
        if ep.name == name:
            client = ep.load()
            if issubclass(client, RpcServer):
                print(f"Loaded RPC client: {name}")
                return client(codec_name, incoming, outgoing)
            else:
                print(f"Invalid RPC client: {name}")
    raise ValueError(f"RPC client not found: {name}")


def create_rpc_codec(
    name: str,
) -> RpcCodec:
    for ep in entry_points(group="streaminghub_datamux.rpc.codec"):
        if ep.name == name:
            client = ep.load()
            if issubclass(client, RpcCodec):
                print(f"Loaded RPC codec: {name}")
                return client()
            else:
                print(f"Invalid RPC codec: {name}")
    raise ValueError(f"RPC codec not found: {name}")
