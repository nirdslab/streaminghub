# PyDFDS

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

PyDFDS is a parser for Data Flow Description Schema (DFDS) metadata, written using Python.

## Installation

```bash

pip install streaminghub-pydfds==0.1.25

```

## Usage

```python

from dfds import Parser
from dfds.typing import Collection, Stream
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
pip-compile -o requirements.txt pyproject.toml
pip-compile --extra dev -o requirements.dev.txt pyproject.toml
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
