# DataMux

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

**DataMux** is a library to stream data into real-time analytics pipelines.
It provides the modes listed below.

* **Proxy Mode**: to interface and proxy live data from sensors
* **Replay Mode**: to replay stored data from datasets
* **Simulate Mode**: to stream guided/unguided mock data for testing

## Installation

```bash

pip install streaminghub-datamux==0.1.3

```

## Usage

### Imports
```python

# Required functions / flags
import datamux.util as util
# Direct API (for running on the same system)
from datamux.api import DataMuxAPI
# Remote API (for running on a remote server)
from datamux.remote.api import DataMuxRemoteAPI

```

### Remote API

```python

server_host = "localhost"
server_port = 3300
api = DataMuxRemoteAPI(rpc_name="websocket", codec_name="json")
await api.connect(server_host, server_port)

```

### Direct API

```python

api = DataMuxAPI()

```

### Listing Available Collections and their Streams
```python

collections = await api.list_collections()
collection_streams = await api.list_collection_streams("name_of_collection")

```

### Replaying a Collection-Stream

```python

# attributes to uniquely identify a recording
attrs = dict({"subject": "A", "session": "1", "task": "1"})
# queue to append replayed data
sink = asyncio.Queue()
# start replaying data into queue
ack = await api.replay_collection_stream("name_of_colelction", "name_of_stream", attrs, sink)
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

### Upgrade a Collection-Stream into LSL Stream

```python

status = await api.publish_collection_stream(collection_name, stream_name, attrs)

```

### List LSL Streams

```python

live_streams = await api.list_live_streams()

```

### Proxy a LSL Stream

```python

# attributes to uniquely identify a LSL stream
attrs = dict({"subject": "19681349", "session": "1", "task": "restEC"})
# queue to append proxied data
sink = asyncio.Queue()
# start proxying LSL data into queue
ack = await api.read_live_stream("stream_name", attrs, sink)
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

## Developer Guide

```bash

# create a virtual environment
python -m venv ~/.virtualenvs/datamux
# activate virtual environment
source ~/.virtualenvs/datamux/bin/activate
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
