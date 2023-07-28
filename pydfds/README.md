# PyDFDS

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

PyDFDS is a parser for Data Flow Description Schema (DFDS) metadata, written using Python.

## Installation

```bash

pip install -U -i https://test.pypi.org/simple/ streaminghub-pydfds

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

## Distribution

```bash

python -m pip install --upgrade pip-tools bumpver build twine
pip-compile pyproject.toml
pip-sync
bumpver update --patch
python -m build
python -m twine check dist/*
python -m twine upload -r testpypi dist/*

```
