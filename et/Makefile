UNAME           = $(shell uname)

ifeq ($(UNAME),Linux)
#PYTHON = /opt/modules/python/2.7/bin/python2.7
PYTHON = /usr/bin/python2
endif

ifeq ($(UNAME),Darwin)
#PYTHON = /usr/local/bin/python
#PYTHON = /usr//bin/python
#PYTHON = /sw//bin/python2.7
#PYTHON = python2
#PYTHON = /opt/local/bin/python2.7
PYTHON = /usr/bin/env python3
endif


# use Butterworth?
SMOOTH = False

# use fixation proximity test (e.g., 5 deg away)?
PROXIMITY = True
#PROXIMITY = False

#WIDTH = 1024
#HEIGHT = 768
#WIDTH = 1280
#HEIGHT = 1024
WIDTH = 1920
HEIGHT = 1200
#HERTZ = 500
HERTZ = 1000
DIST = 21.65 # 55 cm
#SCREEN = 19
SCREEN = 22

BASELINE_T = 2.0
END_T = 180.0
# what I had for testing but we reverted back to 100.0
#VT = 44.0
VT = 200.0

#XTILES = 4
#YTILES = 3
XTILES = 8
YTILES = 4
#XTILES = 8
#YTILES = 6
#XTILES = 8
#YTILES = 8
#XTILES = 16
#YTILES = 12
#XTILES = 16
#YTILES = 16

INDIR  =
IMGDIR =

PLTDIR = ./plots
OUTDIR = ../out
RAWDIR = ../datasets/nback-raw
CSVDIR = ../datasets/nback-csv

#all: dirs raw process graph
#all: process collate
#all: dirs raw process collate stats
#all: dirs raw graph
all: dirs raw process collate
# all: off

off:
	@echo "Currently turned off so as not to trigger the whole run."
	@echo "If you want to, run individual targets, e.g.:"
	@echo "   make dirs"
	@echo "   make raw"
	@echo "   make process"
	@echo "   make collate"
	@echo "   make stats"

dirs:
	mkdir -p data
	mkdir -p data/raw
	mkdir -p plots
	mkdir -p graphs
	mkdir -p figs

raw: rtask rbase

rtask:
	$(PYTHON) ./tsv2raw.py --removeblinks --indir=$(INDIR) --group=task --outdir=$(RAWDIR) --width=$(WIDTH) --height=$(HEIGHT) --dist=$(DIST)

rbase:
	$(PYTHON) ./tsv2raw.py --removeblinks --indir=$(INDIR) --group=baseline --outdir=$(RAWDIR) --width=$(WIDTH) --height=$(HEIGHT) --dist=$(DIST)

process:
	$(PYTHON) ./filter.py --smooth=$(SMOOTH) --indir=$(CSVDIR) --dist=$(DIST) --screen=$(SCREEN) --width=$(WIDTH) --height=$(HEIGHT) --hertz=$(HERTZ) --xtiles=$(XTILES) --ytiles=$(YTILES) --baselineT=$(BASELINE_T) --endT=$(END_T) --vt=$(VT) --proximity=$(PROXIMITY) --outdir=$(OUTDIR)

graph:
	$(PYTHON) ./graph.py --smooth=$(SMOOTH) --indir=$(RAWDIR) --imgdir=$(IMGDIR) --dist=$(DIST) --screen=$(SCREEN) --width=$(WIDTH) --height=$(HEIGHT) --hertz=$(HERTZ) --xtiles=$(XTILES) --ytiles=$(YTILES) --baselineT=$(BASELINE_T) --endT=$(END_T) --vt=$(VT) --proximity=$(PROXIMITY) --outdir=$(OUTDIR) --pltdir=$(PLTDIR) --image="grey-1920x1200.png"

collate:
# 	$(PYTHON) ./collate-amfo.py
# 	$(PYTHON) ./collate-sacc.py
# 	$(PYTHON) ./collate-msac.py
# 	$(PYTHON) ./collate-msrt.py
	$(PYTHON) ./collate-pICA.py
	$(PYTHON) ./collate-pICALH.py
	$(PYTHON) ./collate-pICALH-SG.py
# 	$(PYTHON) ./collate-bpcpd.py
# 	$(PYTHON) ./collate-cbpcpd.py
# 	$(PYTHON) ./collate-fxtn.py
# 	$(PYTHON) ./collate-fxtn-aois.py

stats:
	R --vanilla < analysis_atd.R > analysis_atd.out
	R --vanilla < analysis_nina.R > analysis_nina.out
	R --vanilla < analysis_behavioral.R > analysis_behavioral.out
	R --vanilla < msac-baseline.R > msac-baseline.out
	R --vanilla < msac-task.R > msac-task.out
	R --vanilla < pICALH.R > pICALH.out

lipa:
	R --vanilla < pICALH.R > pICALH.out

clean: 
	rm -f *.pyc 
	rm -rf plots
	rm -rf data
	rm -rf graphs
	rm -rf figs
	rm -f *.out
	rm -f *.pdf
	rm -rf figs/TMS


recreate:
	$(foreach file, $(wildcard $(OUTDIR)/*-fxtn.raw), ./autorun -i $(file) -o $(file) -f $(HERTZ) -n p,0.85,0.4;)
