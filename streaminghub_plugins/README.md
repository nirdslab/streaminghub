# StreamingHub Plugins

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

**Plugins** provide a set of entrypoints to support support different devices, codecs, and remote runtimes for StreamingHub.

## Supported Proxies

* `streaminghub_proxy_empatica_e4` - Empatica E4
* `streaminghub_proxy_lsl` - LabStreamingLayer
* `streaminghub_proxy_pupil_core` - Pupil Core

## Supported Codecs

* `streaminghub_codec_avro` - Avro
* `streaminghub_codec_json` - JSON
* `streaminghub_codec_msgpack` - Msgpack

## Supported RPC Modes

* `streaminghub_rpc_websocket` - Websocket

## Installation

First, find which plugins you need. Next, install them as pip packages.
Some examples are given below.

```bash
pip install streaminghub_codec_avro
pip install streaminghub_codec_json
pip install streaminghub_codec_msgpack
pip install streaminghub_proxy_empatica_e4
pip install streaminghub_proxy_lsl
pip install streaminghub_proxy_pupil_core
pip install streaminghub_rpc_websocket

```

## For Plugin Developers

StreamingHub provides three base classes for extension via plugins.

### Creating New Proxies

Create a python script `my_custom_proxy.py` and define new class which extends the `streaminghub_datamux.Reader` base class.

```python
import streaminghub_datamux as datamux
import streaminghub_pydfds as dfds

class CustomProxy(datamux.Reader[dfds.Node]):
    ...

```

To make this proxy discoverable, define a new entrypoint for `streaminghub_datamux.proxy` in `pyproject.toml`.

```toml
[project.entry-points."streaminghub_datamux.proxy"]
custom_proxy = "my_custom_proxy:CustomProxy"

```

### Creating new Codecs

Create a python script `my_custom_codec.py` and define a new class which extends the `streaminghub_datamux.rpc.RpcCodec` base class.

```python
from streaminghub_datamux.rpc import RpcCodec

class CustomCodec(RpcCodec):
    ...

```

To make this codec discoverable, define a new entrypoint for `streaminghub_datamux.rpc.codec` in `pyproject.toml`.

```toml
[project.entry-points."streaminghub_datamux.rpc.codec"]
custom_codec = "my_custom_codec:CustomCodec"

```

### Creating New RPC Modes

Create a python script `my_custom_rpc.py` and define two new classes which extend the `streaminghub_datamux.rpc.RpcServer` and `streaminghub_datamux.rpc.RpcClient` base classes, respectively.

```python
from streaminghub_datamux.rpc import RpcServer, RpcClient

class CustomServer(RpcServer):
    ...

class CustomClient(RpcClient):
    ...

```

To make this RPC mode discoverable, define new entrypoints for `streaminghub_datamux.rpc.client` and `streaminghub_datamux.rpc.server` in `pyproject.toml`.

```toml
[project.entry-points."streaminghub_datamux.rpc.client"]
custom_rpc = "my_custom_rpc:CustomClient"

[project.entry-points."streaminghub_datamux.rpc.server"]
custom_rpc = "my_custom_rpc:CustomServer"

```
