UNAME  = $(shell uname)
PYTHON = /usr/bin/env python3
R      = /usr/bin/env R

# use Butterworth?
SMOOTH = False

# use fixation proximity test (e.g., 5 deg away)?
PROXIMITY = True

# config for n-back dataset
#DATASET_NAME=n_back
#WIDTH = 1920
#HEIGHT = 1200
#HERTZ = 1000
#DIST = 21.65 # 55 cm
#SCREEN = 22

# config for adhd-sin dataset
DATASET_NAME=adhd_sin
WIDTH = 1920
HEIGHT = 1080
HERTZ = 60
DIST = 20.47 # 52 cm
SCREEN = 21

BASELINE_T = 2.0
END_T = 180.0
# what I had for testing but we reverted back to 100.0
VT = 100.0

XTILES = 8
YTILES = 4

INDIR  =
IMGDIR =

PLTDIR = ./plots
OUTDIR = ../datasets/$(DATASET_NAME)_fxtn
SYNDIR = ../datasets/$(DATASET_NAME)_synt
SYN_NOISE_PROFILE =p,0.85,0.4 # pink noise profile (gain=0.85,alpha=0.4)
#SYN_NOISE_PROFILE =b,1.15 # butterworth noise profile (limit=1.15)
#SYN_NOISE_PROFILE =n # no noise profile
#RAWDIR = ../datasets/$(DATASET_NAME)-raw
CSVDIR = ../datasets/$(DATASET_NAME)

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

prepare:
	$(PYTHON) gen_adhd_sin.py
	#$(PYTHON) gen_n_back.py

synthesis:
	$(foreach file, $(wildcard $(OUTDIR)/*-fxtn.csv), ./autorun -i $(file) -o $(subst _fxtn/,_synt/,$(subst -fxtn.csv,,$(file))) -f $(HERTZ) -n $(SYN_NOISE_PROFILE);)
