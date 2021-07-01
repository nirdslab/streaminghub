const templates = {
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