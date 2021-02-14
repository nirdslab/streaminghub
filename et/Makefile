UNAME  = $(shell uname)
PYTHON = /usr/bin/env python3
R      = /usr/bin/env R

# use Butterworth?
SMOOTH = False

# use fixation proximity test (e.g., 5 deg away)?
PROXIMITY = True
WIDTH = 1920
HEIGHT = 1200
HERTZ = 1000
DIST = 21.65 # 55 cm
SCREEN = 22

BASELINE_T = 2.0
END_T = 180.0
# what I had for testing but we reverted back to 100.0
VT = 100.0

XTILES = 8
YTILES = 4

INDIR  =
IMGDIR =

PLTDIR = ./plots
OUTDIR = ../datasets/n_back_fxn
#RAWDIR = ../datasets/nback-raw
CSVDIR = ../datasets/n_back

#all: dirs raw process graph collate stats
 all: off

off:
	@echo "Currently turned off so as not to trigger the whole run."
	@echo "If you want to, run individual targets, e.g.:"
	@echo "   make dirs"
	@echo "   make raw"
	@echo "   make process"
	@echo "   make graph"
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
	$(R) --vanilla < analysis_atd.R > analysis_atd.out
	$(R) --vanilla < analysis_nina.R > analysis_nina.out
	$(R) --vanilla < analysis_behavioral.R > analysis_behavioral.out
	$(R) --vanilla < msac-baseline.R > msac-baseline.out
	$(R) --vanilla < msac-task.R > msac-task.out
	$(R) --vanilla < pICALH.R > pICALH.out

lipa:
	$(R) --vanilla < pICALH.R > pICALH.out

clean: 
	rm -f *.pyc 
	rm -rf plots
	rm -rf data
	rm -rf graphs
	rm -rf figs
	rm -f *.out
	rm -f *.pdf
	rm -rf figs/TMS

simulate:
	$(foreach file, $(wildcard $(OUTDIR)/*-fxtn.raw), ./autorun -i $(file) -o $(file) -f $(HERTZ) -n p,0.85,0.4;)
