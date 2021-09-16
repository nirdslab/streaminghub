# data source files for simulation
#DATASOURCE=sr_research_eyelink_1000 # n-back
DATASOURCE=tobii_pro_x2_60 # adhd-sin
#DATASOURCE=weather # adhd-sin

replay-n_back:
	PYTHONPATH=src src/datamux/cli/replay.py -n "n_back" -a "subject=S1,S5 task=2back mode=baseline"
replay-adhd_sin:
	PYTHONPATH=src src/datamux/cli/replay.py -n "adhd_sin" -a "subject=003,047 noise=15"
replay-pg_weather:
	PYTHONPATH=src src/datamux/cli/replay.py -n "pg_weather" -a "state=florida"
simulate:
	PYTHONPATH=src src/datamux/cli/simulate.py $(DATASOURCE)
validate:
	PYTHONPATH=src src/datamux/cli/validate.py $(DATASOURCE)
server:
	PYTHONPATH=src STREAMINGHUB_PORT=8765 src/datamux/server.py
workflow:
	node-red
clean:
	rm -rf **/__pycache__