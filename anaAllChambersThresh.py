#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(link,scandate_scurve,scandate_thresh,cName,cType,zTrim):
    import datetime,os,sys
    import subprocess
    from subprocess import CalledProcessError
    from chamberInfo import chamber_config
    from gempython.utils.wrappers import runCommand

    dataPath = os.getenv('DATA_PATH')
    elogPath = "%s/%s"%(os.getenv('ELOG_PATH'),scandate_thresh)
   
    filename_scurve = "%s/%s/trim/z%f/%s/SCurveData_Trimmed/SCurveFitData.root"%(dataPath,cName,zTrim,scandate_scurve)
    filename_thresh = "%s/%s/threshold/channel/%s/ThresholdScanData.root"%(dataPath,cName,scandate_thresh)
    if not os.path.isfile(filename_scurve):
        print "No file containing scurveFitTree to use in analysis. %s does not exist"%(filename_scurve)
        return
    if not os.path.isfile(filename_thresh):
        print "No file to analyze. %s does not exist"%(filename_thresh)
        return

    cmd1 = ["python","%s/vfatqc-python-scripts/macros/anaUltraThreshold.py"%(os.getenv("BUILD_HOME"))]
    cmd1.append("--infilename=%s"%(filename_thresh))
    cmd1.append("--chConfigKnown")
    cmd1.append("--fileScurveFitTree=%s"%(filename_scurve))
    cmd1.append("--vfatmask=0x0")

    cmd2 = ["mkdir","-p","%s"%(elogPath)]
    cmd3 = ["cp","%s/%s/threshold/channel/%s/ThresholdScanData/ThreshPrunedSummary.png"%(dataPath,cName,scandate_thresh),
            "%s/ThreshPrunedSummary_%s.png"%(elogPath,cName)]
    cmd4 = ["cp","%s/%s/threshold/channel/%s/ThresholdScanData/ThreshSummary.png"%(dataPath,cName,scandate_thresh),
            "%s/ThreshSummary_%s.png"%(elogPath,cName)]
    cmd5 = ["cp","%s/%s/threshold/channel/%s/ThresholdScanData/VFATPrunedSummary.png"%(dataPath,cName,scandate_thresh),
            "%s/VFATPrunedSummary_%s.png"%(elogPath,cName)]
    cmd6 = ["cp","%s/%s/threshold/channel/%s/ThresholdScanData/VFATSummary.png"%(dataPath,cName,scandate_thresh),
            "%s/VFATSummary_%s.png"%(elogPath,cName)]    
    cmd7 = ["cp","%s/%s/threshold/channel/%s/ThresholdScanData/VT1MaxSummary.png"%(dataPath,cName,scandate_thresh),
            "%s/VT1MaxSummary_%s.png"%(elogPath,cName)]
    try:
        runCommand(cmd1)
        runCommand(cmd2)
        runCommand(cmd3)
        runCommand(cmd4)
        runCommand(cmd5)
        runCommand(cmd6)
        runCommand(cmd7)
    except CalledProcessError as e:
        print "Caught exception",e
        pass
    return


if __name__ == '__main__':

    import sys,os,signal
    import subprocess
    import itertools
    from multiprocessing import Pool, freeze_support
    from chamberInfo import chamber_config,GEBtype
    from gempython.utils.wrappers import envCheck
    import glob

    from anaoptions import parser

    (options, args) = parser.parse_args()

    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
   
    #Look for threshold scan directory
    searchPath  = "%s/GEMINI*/threshold/channel/*"%(os.getenv('DATA_PATH'))
    dirs        = glob.glob(searchPath)
    foundDir    = False

    for path in dirs:
        if path.rfind(options.scandate1) > 0:
            foundDir = True
            pass
        pass
    if not foundDir:
        print "Unable to find %s in output location specified: %s"%(options.scandate1,searchPath)
        exit(50)
    else:
        print "Found %s"%(options.scandate1)
        pass
    
    #Look for trim directory
    searchPath  = "%s/GEMINI*/trim/z%f/*"%(os.getenv('DATA_PATH'),options.ztrim)
    dirs        = glob.glob(searchPath)
    foundDir    = False

    for path in dirs:
        if path.rfind(options.scandate2) > 0:
            foundDir = True
            pass
        pass
    if not foundDir:
        print "Unable to find %s in output location specified: %s"%(options.scandate2,searchPath)
        exit(51)
    else:
        print "Found %s"%(options.scandate2)
        pass

    freeze_support()
    # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(12)
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
        res = pool.map_async(launch,
                             itertools.izip(chamber_config.keys(),
                                            [options.scandate2  for x in range(len(chamber_config))],
                                            [options.scandate1  for x in range(len(chamber_config))],
                                            [chamber_config[x] for x in chamber_config.keys()],
                                            [GEBtype[x]        for x in chamber_config.keys()],
                                            [options.ztrim     for x in range(len(chamber_config))]
                                            )
                             )
        # timeout must be properly set, otherwise tasks will crash
        print res.get(999999999)
        print("Normal termination")
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
    except Exception as e:
        print("Caught Exception %s, terminating workers"%(str(e)))
        pool.terminate()
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        print("Caught non-Python Exception %s"%(e))
        pool.terminate()
