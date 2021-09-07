# data source files for simulation
DATASOURCE_FILE=datasources/sr_research_eyelink_1000.json # n-back
#DATASOURCE_FILE=datasources/tobii_pro_x2_60.json # adhd-sin
#DATASOURCE_FILE=datasources/weather.json # adhd-sin

replay-n_back:
	tools/datasource_replay.py -n "n_back" -a "subject=S1,S5 task=2back mode=baseline"
replay-adhd_sin:
	tools/datasource_replay.py -n "adhd_sin" -a "subject=003,047 noise=15"
replay-pg_weather:
	tools/datasource_replay.py -n "pg_weather" -a "state=florida"
simulate:
	tools/datasource_simulate.py $(DATASOURCE_FILE)
validate:
	tools/datasource_validate.py $(DATASOURCE_FILE)
proxy:
	PORT=8765 tools/lsl_ws_proxy.py
workflow:
	node-red
clean:
	rm -rf **/__pycache__