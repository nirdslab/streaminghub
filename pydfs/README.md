# streaminghub-pydfs

This package allows using Dataset File System (DFS) within StreamingHub projects.

## Installation

```bash
python -m pip install streaminghub-dfs
```

## Usage

```python
import pydfs as dfs

datasource_spec: dfs.DataSourceSpec = dfs.get_datasource_spec()
dataset_spec: dfs.DataSetSpec = dfs.get_dataset_spec()
analytic_spec: dfs.AnalyticSpec = dfs.get_analytic_spec()

dfs.create_outlet()
```