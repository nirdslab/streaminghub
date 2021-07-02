interface Info {
  timestamp: string;
  version: string;
  checksum: string;
}

interface Field {
  name: string;
  description: string;
  dtype: string;
}

interface Stream {
  name: string;
  index: string;
  description: string;
  unit: string;
  frequency: string;
  channels: string[];
}

interface Author {
  name: string;
  affiliation: string;
  email: string;
}

interface Group {
  description: string;
  attributes: string[];
}

export interface Datasource {
  $schema: string;
  info: Info;
  device: {
    model: string;
    manufacturer: string;
    category: string;
  };
  fields: { [id: string]: Field };
  streams: { [id: string]: Stream };
}

export interface Dataset {
  $schema: string;
  name: string;
  description: string;
  keywords: string[];
  authors: Author[];
  groups: { [id: string]: Group };
  info: Info;
  sources: { [id: string]: string };
  fields: { [id: string]: Field };
  resolver: string;
}

export interface Analytic {
  $schema: string;
  info: Info;
  sources: { [id: string]: string };
  fields: { [id: string]: Field };
  inputs: { [id: string]: string };
  streams: { [id: string]: Stream };
}

export const templates = {
  "datasource": {
    "$schema": "https://raw.githubusercontent.com/nirdslab/streaminghub/master/dfs/datasource.schema.json",
    "info": {
      "timestamp": "",
      "version": "",
      "checksum": ""
    },
    "device": {
      "model": "",
      "manufacturer": "",
      "category": ""
    },
    "fields": {},
    "streams": {}
  },
  "dataset": {
    "$schema": "https://raw.githubusercontent.com/nirdslab/streaminghub/master/dfs/dataset.schema.json",
    "name": "",
    "description": "",
    "keywords": [],
    "authors": [],
    "groups": {},
    "info": {
      "timestamp": "",
      "version": "",
      "checksum": ""
    },
    "sources": {},
    "fields": {},
    "resolver": ""
  },
  "analytic": {
    "$schema": "https://raw.githubusercontent.com/nirdslab/streaminghub/master/dfs/analytic.schema.json",
    "info": {
      "timestamp": "",
      "version": "",
      "checksum": ""
    },
    "sources": {},
    "fields": {},
    "inputs": {},
    "streams": {}
  }
}
export default templates;