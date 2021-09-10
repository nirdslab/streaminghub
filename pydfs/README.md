# PyDFS

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

This package allows using Dataset File System (DFS) within StreamingHub projects.

## Installation

```bash
cd pydfs/
python -m pip install -e .
```

## Usage

```python
import dfs

datasource_spec = dfs.get_datasource_spec("name_of_datasource")
dataset_spec = dfs.get_dataset_spec("name_of_dataset")
analytic_spec = dfs.get_analytic_spec("name_of_analytic")

dfs.create_outlet(
  "some_unique_id",
  "device_info_from_datasource_metadata",
  "stream_info_from_datasource_metadata"
)
```