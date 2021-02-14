# variables for n-back dataset
DATASET_FILE=n_back
DATASOURCE_FILE=datasources/sr_research_eyelink_1000.json
REPLAY_ARGS="subject=S1,S5 task=2back mode=baseline"

# variables for adhd_sin dataset
#DATASET_FILE=adhd_sin
#DATASOURCE_FILE=datasources/tobii_pro_x2_60.json
#REPLAY_ARGS="subject=003,047 noise=15"

PROXY_PORT=8765

replay:
	tools/datasource_replay.py -n $(DATASET_FILE) -a $(REPLAY_ARGS)
simulate:
	tools/datasource_simulate.py $(DATASOURCE_FILE)
validate:
	tools/datasource_validate.py $(DATASOURCE_FILE)
proxy:
	PORT=$(PROXY_PORT) tools/lsl_ws_proxy.py
workflow:
	node-red