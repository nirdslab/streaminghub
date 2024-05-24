# StreamingHub Plugins

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

**Plugins** provide a set of entrypoints to support support different devices, codecs, and remote runtimes for StreamingHub.

## Supported Proxies

** Empatica E4
** LabStreamingLayer
\*\* Pupil Core

## Supported Codecs

** Avro
** JSON
\*\* Msgpack

## Supported RPC Modes

\*\* Websocket

## Installation

First, install plugins as a pip package. This will install all Proxies, Codecs, and RPC Modes shown above.

```bash

pip install streaminghub-plugins==0.0.1

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

Create a python script `my_custom_rpc.py` and define two new classes which extend the `streaminghub_datamux.rpc.RpcServer` and `streaminghub_datamux.rpc.RpcCodec` base classes, respectively.

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

## Copyright

```
Copyright (c) 2023 Old Dominion University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

This work shall be cited in the bibliography as:

    Yasith Jayawardana, Vikas G. Ashok, and Sampath Jayarathna. 2022.
    StreamingHub: interactive stream analysis workflows. In Proceedings of
    the 22nd ACM/IEEE Joint Conference on Digital Libraries (JCDL '22).
    Association for Computing Machinery, New York, NY, USA, Article 15, 1-10.
    https://doi.org/10.1145/3529372.3530936

    Yasith Jayawardana and Sampath Jayarathna. 2020. Streaming Analytics and
    Workflow Automation for DFS. In Proceedings of the 20th ACM/IEEE Joint
    Conference on Digital Libraries (JCDL '20).
    Association for Computing Machinery, New York, NY, USA, 513-514.
    https://doi.org/10.1145/3383583.3398589

    Yasith Jayawardana and Sampath Jayarathna. 2019. DFS: A Dataset File
    System for Data Discovering Users. In Proceedings of the 19th ACM/IEEE
    Joint Conference on Digital Libraries in 2019 (JCDL '19).
    Association for Computing Machinery, New York, NY, USA, 355-356.
    https://doi.org/10.1109/JCDL.2019.00068

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```
