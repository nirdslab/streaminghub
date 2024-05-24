# DataMux

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

**DataMux** is a library to stream data into real-time analytics pipelines.
It provides the modes listed below.

- **Proxy Mode**: to interface and proxy live data from sensors
- **Replay Mode**: to replay stored data from datasets
- **Simulate Mode**: to stream guided/unguided mock data for testing

## Installation

First, install datamux as a pip package.

```bash

pip install streaminghub-datamux==0.1.7

```

## Initialization

Next, configure where datamux should look for data and metadata.
The configuration is stored at `~/.streaminghubrc`.

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
