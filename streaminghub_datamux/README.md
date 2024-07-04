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

pip install streaminghub-datamux

```

## Initialization

Next, configure where datamux should look for data and metadata. We use `$HOME/streaminghub` by default. This configuration will be stored at `$HOME/.streaminghubrc`.

```bash

python -m streaminghub_datamux init --data_dir="$HOME/streaminghub" --meta_dir="$HOME/streaminghub"

```

## Usage

### Import and Setup

In your Python script, first import datamux as follows.

```python
# import datamux
import streaminghub_datamux as dm

```

Next, instantiate the Datamux API. Here, you have two options:

```python
# Option A - Local API (runs locally)
api = dm.API()

# Option B - Remote API (runs over a remote datamux server)
api = dm.RemoteAPI(rpc_name="<rpc>", codec_name="<codec>")
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

## Start a Remote API

You can start a remote API using the command below.

```bash
python -m streaminghub_datamux serve -H "<host_name>" -p <port> -r <rpc_name> -c <codec_name>
```

## For Developers

```bash

# clone streaminghub from git
git clone https://github.com/nirdslab/streaminghub.git

# cd into streaminghub/ directory
cd streaminghub/

# install the streaminghub_datamux/ folder as a pip package
python -m pip install -e streaminghub_datamux/

```
