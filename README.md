# StreamingHub

<img src="https://i.imgur.com/xSieE3V.png" height="100px"><br>
StreamingHub is a framework for developing real-time bio-signal analysis workflows.<br>
<img src="assets/demo-animated.gif" width="100%">

It provides the following components:

## DFDS | `dfds/`

JSON schemas to describe data streams, data sets, and analytics, along with a few samples.`<br>`
**Technologies:** JSON, JSON Schema

## PyDFDS | `pydfds/`

A Python package to read DFDS-annotated datasets and their metadata.`<br>`
**Technologies:** Python, Pydantic, JSONSchema, Pydantic

## Curator | `curator/`

A Web interface to annotate files with DFDS metadata and rearranging them in a standard form.`<br>`
**Technologies:** Python, Flask, PyDFDS

## DataMux | `datamux/`

A Python package providing a high-level API to read bio-signal streams.
It supports three modes:
(a) relaying real-time sensory data,
(b) replaying recordings from datasets, and
(c) simulating mock data as test cases.`<br>`
**Technologies:** Python, PyLSL, WebSockets

## FlowMaker | `flowmaker/`

Node-RED addons for using DataMux APIs and visualizing bio-signal data within Node-RED.`<br>`
**Technologies:** Javascript, JSON, Vega

## Repository | `repository/`

A collection of DFDS metadata for commonly used bio-signal datasets and eye-trackers.`<br/>`
**Technologies:** JSON, DFDS

## Examples | `examples/`

A set of real-time bio-signal analysis experiments built upon StreamingHub.`<br/>`
**Technologies:** Python, DataMux, OpenGL

## Archived | `archived/`

An archive of abandoned projects.`<br/>`
**Technologies:** Python, Flask, Angular

## Install from Source (for Development)

### Option 1 - Micromamba

We recommend using `micromamba` to seamlessly install both python and non-python dependencies.

```bash
# clone the repository
git clone git@github.com:nirdslab/streaminghub.git

# cd into project directory
cd streaminghub/

# install micromamba (recommended)
"${SHELL}" <(curl -L https://micro.mamba.pm/install.sh)

# create an environment with required dependencies
micromamba env create -n streaminghub --file environment.yml

# activate environment
micromamba activate streaminghub
```

### Option 2 - Pip

If using `streaminghub` for an existing project, you can directly install the required components via `pip`.

```bash
# clone the repository
git clone git@github.com:nirdslab/streaminghub.git

# install curator (from source)
pip install -e streaminghub/curator

# install pydfds (from source)
pip install -e streaminghub/pydfds

# install datamux (from source)
pip install -e streaminghub/datamux

```

## Install from PyPI

If your plan to use `streaminghub`, without modifying/extending functionality, please install the published versions from `pip`.

```bash

# install curator (from PyPI)
pip install streaminghub_curator

# install pydfds (from PyPI)
pip install streaminghub_pydfds

# install datamux (from PyPI)
pip install streaminghub_datamux

```

## Running the Project

```bash
# starting streaminghub curator
python -m streaminghub_curator --host=<HOSTNAME> --port=<PORT>

# starting datamux server (for streaming live data)
python -m streaminghub_datamux
```

## Citation

If you found this work useful in your research, please consider citing us.

```bibtex
@inproceedings{jayawardana2021streaminghub,
author       = {Jayawardana, Yasith and Jayawardena, Gavindya and Duchowski, Andrew T. and Jayarathna, Sampath},
title        = {Metadata-Driven Eye Tracking for Real-Time Applications},
year         = {2021},
isbn         = {9781450385961},
publisher    = {Association for Computing Machinery},
address      = {New York, NY, USA},
doi          = {10.1145/3469096.3474935},
booktitle    = {Proceedings of the 21st ACM Symposium on Document Engineering},
articleno    = {22},
numpages     = {4},
location     = {Limerick, Ireland},
series       = {DocEng '21}
}
@inproceedings {jayawardana2020streaminghub
author       = {Jayawardana, Yasith and Jayarathna, Sampath},
title        = {Streaming Analytics and Workflow Automation for DFDS},
doi          = {10.1145/3383583.3398589},
pages        = {513–514},
location     = {Virtual Event, China},
series       = {JCDL '20},
year         = {2020},
publisher    = {Association for Computing Machinery},
address      = {New York, NY, USA}
}
```
