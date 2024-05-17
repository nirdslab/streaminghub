# DataMux

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

**DataMux** is a library to stream data into real-time analytics pipelines.
It provides the modes listed below.

* **Proxy Mode**: to interface and proxy live data from sensors
* **Replay Mode**: to replay stored data from datasets
* **Simulate Mode**: to stream guided/unguided mock data for testing

## Installation

First, install datamux as a pip package.

```bash

pip install streaminghub-datamux==0.1.7

```

## Initialization

Next, configure where datamux should look for data and metadata.
The configuration is stored at ``~/.streaminghubrc``.

```bash

python -m datamux init --data_dir="<path/to/dataset/dir>" --meta_dir="<path/to/metadata/dir>"

```

## Usage

### Basic Setup

First, import datamux from a python script

```python
# import datamux
import streaminghub_datamux as datamux

```

Next, instantiate the Datamux API. Here, you have two options:

```python
# Option 1 - Local API (runs locally)
api = datamux.API()

# Option 2 - Remote API (runs over a remote datamux server)
api = datamux.RemoteAPI(rpc_name="<rpc>", codec_name="<codec>")
await api.connect(server_host="<host>", server_port=<port>)
```

### Replay Recordings from Collections

```python
# list all collections (each collection provides one or more streams)
collections = await api.list_collections()
# list all recordings (i.e., streams) in a collection, by id
streams = await api.list_collection_streams(collection_id="<id>")
# sample attributes of a stream (found in stream.attrs)
attrs = dict({"subject": "A", "session": "1", "task": "1"})
# queue to append received data
sink = asyncio.Queue()
# start gathering data into queue
ack = await api.replay_collection_stream(collection_id="<id>", stream_id="<id>", attrs, sink)
# each request is assigned a unique ID for later reference
assert ack.randseq is not None
# simply await the queue to read data
while True:
    item = await sink.get()
    # checking for end-of-stream
    if item == util.END_OF_STREAM:
        break
# once done, stop the task to avoid wasting resources
await api.stop_task(ack.randseq)
```

### Proxy Live Streams from Devices

```python
# list all nodes (each node provides one or more streams)
nodes = await api.list_live_nodes()
# list all devices (i.e., streams) in a node, by id
streams = await api.list_live_streams(node_id="<id>")
# sample attributes of a stream (found in stream.attrs)
attrs = dict({"subject": "A", "session": "1", "task": "1"})
# queue to append received data
sink = asyncio.Queue()
# start gathering data into queue
ack = await api.proxy_live_stream(node_id="<id>", stream_id="<id>", attrs, sink)
# each request is assigned a unique ID for later reference
assert ack.randseq is not None
# simply await the queue to read data
while True:
    item = await sink.get()
    # checking for end-of-stream
    if item == util.END_OF_STREAM:
        break
# once done, stop the task to avoid wasting resources
await api.stop_task(ack.randseq)

```

### Publish Recordings over LSL

```python

status = await api.publish_collection_stream(collection_name, stream_name, attrs)

```

## Start a Remote API

You can start a remote API using the command below.

```bash
python -m datamux serve -H "<host_name>" -p <port> -r <rpc_name> -c <codec_name>
```

## Developer Guide

```bash

# goto datamux/ directory
cd datamux/
# install pip tools
python -m pip install --upgrade pip-tools
# generate requirements.txt
pip-compile --strip-extras -o requirements.txt pyproject.toml
pip-compile --strip-extras --extra dev -o requirements.dev.txt pyproject.toml
# install dependencies
pip-sync requirements.txt requirements.dev.txt
# update version (--patch or --minor or --major)
bumpver update --patch
# build package
python -m build
# check package
python -m twine check dist/*
# publish package (testpypi)
python -m twine upload -r testpypi dist/*
# publish package (pypi)
python -m twine upload dist/*

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
