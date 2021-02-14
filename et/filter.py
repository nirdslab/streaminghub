#!/usr/bin/env python3

# this file is the driver for the python analysis script

import getopt
import glob
import os
import sys

from model.monitor import Monitor
from model.process import Process


def usage():
    print("Usage: python filter.py "
          " --width=? --height=? --screen=? --dist=?"
          " --xtiles=? --ytiles=?\n"
          " --indir=? --outdir=?\n"
          " --file=?\n"
          " --hertz=?\n"
          " --sfdegree=? --sfcutoff=?\n"
          " --dfdegree=? --dfwidth=?\n"
          " --vt=?\n"
          " --baselineT=? --endT=?\n"
          " --smooth=?\n"
          " --proximity=?\n"
          "   width, height: screen dimensions (in pixels)\n"
          "   screen: screen diagonal dimension (in inches)\n"
          "   dist: viewing distance (in inches)\n"
          "   xtiles: number of AOI tiles (in x direction)\n"
          "   ytiles: number of AOI tiles (in y direction)\n"
          "   indir: a directory containing input files to be processed\n"
          "   outdir: a directory containing output files\n"
          "   file: a single file to process\n"
          "   hertz: the sampling rate of the data\n"
          "   sfdegree: butterworth filter smoothing degree \n"
          "   sfcutoff: butterworth filter smoothing cutoff \n"
          "   dfdegree: savitzky-golay filter degree \n"
          "   dfwidth: savitzky-golay filter width \n"
          "   vt: min velocity for change to be a saccade\n"
          "   baselineT: time for pupil diameter baseline\n"
          "   endT: max time to average pupil diameter difference\n"
          "   smooth: True enables butterworth smoothing\n"
          "   proximity: fixation proximity check\n")


def main(argv):
    args = ['width=', 'height=', 'screen=', 'dist=', 'xtiles=', 'ytiles=',
            'indir=', 'outdir=', 'file=', 'hertz=', 'sfdegree=', 'sfcutoff=',
            'dfdegree=', 'dfwidth=', 'vt=', 'baselineT=', 'endT=', 'smooth=', 'proximity=']
    try:
        opts, args = getopt.getopt(argv, '', args)
    except getopt.GetoptError as e:
        print(e, file=sys.stderr)
        usage()
        return exit(1)

    # initialize vars to None
    width = height = screen = dist = xtiles = ytiles = indir = outdir = file = hertz = sfdegree = sfcutoff = dfdegree = dfwidth = vt = baseline_t = end_t = smooth = proximity = None

    # parse args into vars
    for opt, arg in opts:
        opt = opt.lower()
        if opt != '--file':
            arg = arg.lower()

        if opt == '--width':
            width = arg
        elif opt == '--height':
            height = arg
        elif opt == '--screen':
            screen = float(arg)
        elif opt == '--dist':
            dist = float(arg)
        elif opt == '--xtiles':
            xtiles = int(arg)
        elif opt == '--ytiles':
            ytiles = int(arg)
        elif opt == '--indir':
            indir = arg
        elif opt == '--outdir':
            outdir = arg
        elif opt == '--file':
            file = arg
        elif opt == '--hertz':
            hertz = float(arg)
        elif opt == '--sfdegree':
            sfdegree = float(arg)
        elif opt == '--sfcutoff':
            sfcutoff = float(arg)
        elif opt == '--dfdegree':
            dfdegree = float(arg)
        elif opt == '--dfwidth':
            dfwidth = float(arg)
        elif opt == '--vt':
            vt = float(arg)
        elif opt == '--baselinet':
            baseline_t = float(arg)
        elif opt == '--endt':
            end_t = float(arg)
        elif opt == '--smooth':
            if arg == 'true':
                smooth = True
            elif arg.lower() == 'false':
                smooth = False
            else:
                raise Exception("Invalid arg for --smooth.")
        elif opt == '--proximity':
            if arg == 'true':
                proximity = True
            elif arg.lower() == 'false':
                proximity = False
            else:
                raise Exception("Invalid arg for --proximity")

    # (default) differentiation (SG) filter parameters: width, degree, order
    if dfwidth is None and dfdegree is None:
        if smooth:
            dfwidth = 3
            dfdegree = 2
        else:
            dfwidth = 5
            dfdegree = 3
    dfo = 1

    # (default) smoothing (Butterworth) filter parameters: degree, cutoff
    if sfdegree is None:
        sfdegree = 3
    if sfcutoff is None and hertz is not None:
        sfcutoff = 1.0 / hertz  # must be 0 < Wn < 1

    if None in [width, height, screen, dist, xtiles, ytiles, indir, outdir, hertz, sfdegree, sfcutoff, dfdegree, dfwidth, vt, baseline_t, end_t, smooth, proximity]:
        print("Some args are not initialized", file=sys.stderr)
        return exit(1)

    # get .csv input files to process
    if os.path.isdir(indir):
        files = glob.glob('%s/*.csv' % indir)
    else:
        files = []

    # if user specified --file="..." then we use that as the only one to process
    if file is not None:
        file = indir + file
        if os.path.isfile(file):
            files = [file]
            print("overriding files with: ", files)

    # declare monitor
    monitor = Monitor(int(width), int(height), screen, dist)

    # model loop, we iterate over .csv files
    for file in files:
        # don't process empty files
        if os.path.getsize(file) == 0:
            continue

        #   base = os.path.basename(file)
        path, base = os.path.split(file)

        print("Processing: ", file, "[", base, "]")

        # split filename from extension
        filename, ext = os.path.splitext(base)

        print("path: %s, base: %s, filename: %s, ext: %s" % (path, base, filename, ext))
        subj = filename.split('-')[0]
        group = filename.split('-')[1]
        # block = filename.split('-')[2] # removed for convenience
        task = filename.split('-')[2]
        typ = filename.split('-')[3]
        print("subj: %s, group: %s, task: %s, type: %s" % (subj, group, task, typ))

        process = Process(width, height, screen, dist, hertz)
        process.parse_file(file)
        process.smooth(sfdegree, sfcutoff, smooth)
        process.differentiate(dfwidth, dfdegree, dfo)
        process.threshold(vt, monitor, typ, proximity)
        process.write_threshold_to_file("%s/%s-fxtn%s" % (outdir, filename, ".csv"))
        del process


if __name__ == "__main__":
    main(sys.argv[1:])
