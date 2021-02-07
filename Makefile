DATASET_FILE="adhd_sin"
DATASOURCE_FILE="datasources/tobii_pro_x2_60.json"
PROXY_PORT=8765

replay:
	tools/datasource_replay.py -n $(DATASET_FILE)
simulate:
	tools/datasource_simulate.py $(DATASOURCE_FILE)
validate:
	tools/datasource_validate.py $(DATASOURCE_FILE)
proxy:
	PORT=$(PROXY_PORT) tools/lsl_ws_proxy.py
workflow:
	node-red