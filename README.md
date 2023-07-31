# StreamingHub

<img src="https://i.imgur.com/xSieE3V.png" height="100px"><br>
StreamingHub is a visual programming framework to simplify data analysis workflows.<br>
<img src="archived/assets/demo-animated.gif" width="100%">

This repository hosts the following modules,

## DFDS | `dfds/`

JSON schemas to describe data streams, data sets, and analytics, along with a few samples.<br>
**Technologies:** JSON, JSON Schema

## PyDFDS | `pydfds/`

A Python package for using DFDS in StreamingHub projects.
**Technologies:** Python, PyLSL

## DataMux | `datamux/`

Scripts to stream sensory data in real-time, replay stored data from datasets, and stream mock data for testing.<br>
**Technologies:** Python, PyLSL, WebSockets

## Node-RED Addons | `node-red-addons/`

Node-RED support package to use StreamingHub.<br>
It adds widgets to discover data streams, display metadata, auto-populate
**Technologies:** Javascript, JSON, Vega

## Experimental | `experimental/`

Streaminghub modules that are still in experimental stage.
These modules aim to improve the architecture and performance of streaminghub, and would likely be promoted into core 
streaminghub modules in the future.<br/>

## Projects
A collection of projects conducted using StreamingHub for different use cases.<br/>
**Technologies:** DFDS, JSON, Python, OpenGL

## Archived Projects

### Orange3 Addons | `old/orange3-addons`

Orange3 support package to use StreamingHub.<br>
It adds widgets to discover data streams, display their metadata, and subscribe to them.<br>
**Technologies:** Python, PyQt5, Orange3, PyLSL.

### WebUI | `old/webui`

Web interface to generate and validate DFDS metadata.<br>
**Technologies:** Angular, Typescript, Monaco Editor

### Old WebUI | `old/webui-old`

Web interface to generate and validate DFDS metadata.<br>
**Technologies:** Angular, Typescript, Monaco Editor

<hr/>

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
