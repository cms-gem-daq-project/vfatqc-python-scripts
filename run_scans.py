#!/bin/env python

def launchTests(args):
  return launchTestsArgs(*args)

def launchTestsArgs(tool, slot, link, chamber,vt1=None,vt2=0,perchannel=False,trkdata=False,ztrim=4.0):
  import datetime,os,sys
  import subprocess
  from subprocess import CalledProcessError
  from chamberInfo import chamber_config

  scanType = "vt1"
  dataType = "VT1Threshold"

  preCmd = None
  if tool == "ultraScurve.py":
    scanType = "scurve"
    dataType = "SCurve"
    if vt1 in range(256):
      cmd.append("--vt1=%d"%(vt1))
      pass
    preCmd = ["confChamber.py","-s%d"%(slot),"-g%d"%(link)]
    pass
  elif tool == "trimChamber.py":
    scanType = "trim"
    dataType = None
    pass

  startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  log = file("%s_scan_%s_%s.log"%(chamber,scanType,startTime),"w")
  cmd = ["%s"%(tool),"-s%d"%(slot),"-g%d"%(link)]

  if tool == "trimChamber.py":
    cmd.append("--ztrim=%f"%(ztrim))
    if vt1 in range(256):
      cmd.append("--vt1=%d"%(vt1))
      pass
    pass
  else:
    cmd.append("--filename=%sData_%s_%s.root"%(dataType,chamber,startTime))
    if tool is "ultraThreshold.py":
      if vt2 in range(256):
        cmd.append("--vt2=%d"%(vt2))
        pass
      if perchannel:
        cmd.append("--perchannel")
        pass
      if trkdata:
        cmd.append("--trkdata")
        pass
      pass
    pass
  try:
    if preCmd:
      try:
        print "executing", preCmd
        sys.stdout.flush()
        returncode = subprocess.call(preCmd,stdout=log)
        print "%s had return code %d"%(preCmd,returncode)
      except CalledProcessError as e:
        print "Caught exception",e
        pass
      pass
    print "executing", cmd
    sys.stdout.flush()
    returncode = subprocess.call(cmd,stdout=log)
    print "%s had return code %d"%(cmd,returncode)
  except CalledProcessError as e:
    print "Caught exception",e
    pass
  return

if __name__ == '__main__':

  import sys,os
  import subprocess
  import itertools
  from multiprocessing import Pool, freeze_support

  from qcoptions import parser

  parser.add_option("--parallel", action="store_true", dest="parallel",
                    help="Run tests in parllel (default is false)", metavar="parallel")
  parser.add_option("--tool", type="string", dest="tool",default="ultraThreshold.py",
                    help="Tool to run (scan or analyze", metavar="tool")
  parser.add_option("--vt2", type="int", dest="vt2", default=0,
                    help="Specify VT2 to use", metavar="vt2")
  parser.add_option("--perchannel", action="store_true", dest="perchannel",
                    help="Run a per-channel VT1 scan", metavar="perchannel")
  parser.add_option("--trkdata", action="store_true", dest="trkdata",
                    help="Run a per-VFAT VT1 scan using tracking data (default is to use trigger data)", metavar="trkdata")
  parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                  help="Specify the p value of the trim", metavar="ztrim")

  (options, args) = parser.parse_args()

  if options.tool not in ["trimChamber.py","ultraThreshold.py","ultraScurve.py"]:
    print "Invalid tool specified"
    exit(1)

  threads = []

  print itertools.izip([options.tool for x in range(len(chamber_config))],
                       [options.slot for x in range(len(chamber_config))],
                       chamber_config.keys(),
                       chamber_config.values(),
                       [options.vt2 for x in range(len(chamber_config))],
                       [options.perchannel for x in range(len(chamber_config))],
                       [options.trkdata for x in range(len(chamber_config))],
                       [options.ztrim for x in range(len(chamber_config))]
                       )

  if options.parallel:
    print "Running jobs in parallel mode"
    freeze_support()
    pool = Pool(10)
    res = pool.map(launchTests,
                   itertools.izip([options.tool for x in range(len(chamber_config))],
                                  [options.slot for x in range(len(chamber_config))],
                                  chamber_config.keys(),
                                  chamber_config.values(),
                                  [options.vt2 for x in range(len(chamber_config))],
                                  [options.perchannel for x in range(len(chamber_config))],
                                  [options.trkdata for x in range(len(chamber_config))],
                                  [options.ztrim for x in range(len(chamber_config))]
                                  )
                   )
    print res
    pass
  else:
    print "Running jobs in serial mode"
    for link in chamber_config.keys():
      chamber = chamber_config[link]
      launchTests(options.tool,options.slot,link,chamber,options.vt2,options.perchannel,options.trkdata,options.ztrim)
      pass
    pass
