# Streaminghub

<img src="https://i.imgur.com/xSieE3V.png" height="100px">

This repository hosts the implementation of streaming-hub, a visual programming toolkit built on DFS to simplify data analysis workflows.
It the following subprojects,
* dfs
* conduit
* orange
* webui

## DFS


## Conduit
Conduit is a collection of connectors for reading data from sensory devices, and publishing them as LSL streams, annotated with DFS metadata.
It currently supports the following devices:
* Empatica E4 (ongoing)
* Pupil Core (ongoing)
* CGX Quick-30 (TBD)
We are working on adding more devices, and streamlining the metadata format to better provide data semantics.

## Orange
Orange Streaming is a Python package that adds support for DFS data-streams in Orange3.
It provides a set of widgets to read data-streams from LSL, and their metadata in compliance with the original meta-stream and meta-file specifications.

## WebUI


