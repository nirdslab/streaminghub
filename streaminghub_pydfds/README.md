# PyDFDS

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

PyDFDS is a parser for Data Flow Description Schema (DFDS) metadata, written using Python.

## Installation

```bash

pip install streaminghub-pydfds==0.1.35

```

## Usage

```python

from streaminghub_pydfds import Parser
from streaminghub_pydfds.typing import Collection, Stream
from util import restream_data

# define a DFDS parser
parser = Parser()

# open a DFDS collection
fp = "/path/to/collection.json"
collection = parser.get_collection_metadata(fp)
dataloader = collection.dataloader()

# list all items in the collection
for attrs in dataloader.ls():
  for stream_id, stream in collection.streams.items():
      pass

# read an entire recording at once
attrs, data = dataloader.read(stream.attrs)

# or replay the recording as a stream
asyncio.create_task(replay_data(collection, stream))

return streams

```

## Developer Guide

```bash

# create a virtual environment
python -m venv ~/.virtualenvs/pydfds
# activate virtual environment
source ~/.virtualenvs/pydfds/bin/activate
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
