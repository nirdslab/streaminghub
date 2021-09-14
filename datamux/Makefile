# data source files for simulation
DATASOURCE_FILE=datasources/sr_research_eyelink_1000.json # n-back
#DATASOURCE_FILE=datasources/tobii_pro_x2_60.json # adhd-sin
#DATASOURCE_FILE=datasources/weather.json # adhd-sin

replay-n_back:
	PYTHONPATH=src src/datamux/replay.py -n "n_back" -a "subject=S1,S5 task=2back mode=baseline"
replay-adhd_sin:
	PYTHONPATH=src src/datamux/replay.py -n "adhd_sin" -a "subject=003,047 noise=15"
replay-pg_weather:
	PYTHONPATH=src src/datamux/replay.py -n "pg_weather" -a "state=florida"
simulate:
	PYTHONPATH=src src/datamux/simulate.py $(DATASOURCE_FILE)
validate:
	PYTHONPATH=src src/datamux/validate.py $(DATASOURCE_FILE)
server:
	PYTHONPATH=src STREAMINGHUB_PORT=8765 src/datamux/server.py
workflow:
	node-red
clean:
	rm -rf **/__pycache__