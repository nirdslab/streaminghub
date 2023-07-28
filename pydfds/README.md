# PyDFDS

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

PyDFDS is a parser for Data Flow Description Schema (DFDS) metadata, written using Python.

## Installation

```bash

python -m pip install -U -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ streaminghub-pydfds

```

## Usage

```python

import dfds

datasource_spec = dfds.get_datasource_spec("name_of_datasource")
dataset_spec = dfds.get_dataset_spec("name_of_dataset")
analytic_spec = dfds.get_analytic_spec("name_of_analytic")

dfds.create_outlet_for_stream(
  "some_unique_id",
  "device_info_from_datasource_metadata",
  "stream_info_from_datasource_metadata"
)

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
