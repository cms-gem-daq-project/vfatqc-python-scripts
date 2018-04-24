#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(tool, shelf, slot, link, chamber, vfatmask, scanmin, scanmax, nevts, stepSize=1,
               vt1=None,vt2=0,mspl=None,perchannel=False,trkdata=False,ztrim=4.0,
               config=False,amc13local=False,t3trig=False, randoms=0, throttle=0,
               internal=False, debug=False):
  import datetime,os,sys
  import subprocess
  from subprocess import CalledProcessError
  from gempython.gemplotting.mapping.chamberInfo import chamber_config
  from gempython.utils.wrappers import runCommand

  startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  dataPath = os.getenv('DATA_PATH')

  scanType = "vt1"
  dataType = "VT1Threshold"

  #Build Commands
  setupCmds = []
  preCmd = None
  cmd = ["%s"%(tool),"-s%i"%(slot),"-g%i"%(link),"--shelf=%i"%(shelf), "--nevts=%i"%(nevts), "--vfatmask=0x%x"%(vfatmask)]
  if debug:
    cmd.append( "--debug")
  if tool == "ultraScurve.py":
    scanType = "scurve"
    dataType = "SCurve"
    dirPath = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/SCurveData.root"%dirPath )
    if mspl:
      cmd.append( "--mspl=%i"%(mspl) )
    preCmd = ["confChamber.py","-s%i"%(slot),"-g%i"%(link),"--shelf=%i"%(shelf)]
    if vt1 in range(256):
      preCmd.append("--vt1=%d"%(vt1))
      pass
    pass
  elif tool == "trimChamber.py":
    scanType = "trim"
    dataType = None
    preCmd = ["confChamber.py","-s%i"%(slot),"-g%i"%(link),"--shelf=%i"%(shelf)]
    if vt1 in range(256):
      preCmd.append("--vt1=%d"%(vt1))
      pass
    dirPath = "%s/%s/%s/z%f/"%(dataPath,chamber_config[link],scanType,ztrim)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append("--ztrim=%f"%(ztrim))
    if vt1 in range(256):
      cmd.append("--vt1=%d"%(vt1))
      pass
    cmd.append( "--dirPath=%s"%dirPath )
    pass
  elif tool == "ultraThreshold.py":
    scanType = "threshold"
    if vt2 in range(256):
      cmd.append("--vt2=%d"%(vt2))
      pass
    if perchannel:
      cmd.append("--perchannel")
      scanType = scanType + "/channel"
      pass
    else:
      scanType = scanType + "/vfat"
      if trkdata:
        cmd.append("--trkdata")
        scanType = scanType + "/trk"
        pass
      else:
        scanType = scanType + "/trig"
        pass
      pass
    dirPath = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/ThresholdScanData.root"%dirPath )
    pass
  elif tool == "fastLatency.py":
    scanType = "latency/trig"
    dirPath = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/FastLatencyScanData.root"%dirPath )
    if mspl:
      cmd.append( "--mspl=%d"%(mspl) )
    pass
  elif tool == "ultraLatency.py":
    scanType = "latency/trk"
    dirPath = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/LatencyScanData.root"%dirPath )
    cmd.append( "--scanmin=%d"%(scanmin) )
    cmd.append( "--scanmax=%d"%(scanmax) )
    cmd.append( "--throttle=%i"%(throttle) )
    if stepSize > 0:
      cmd.append( "--stepSize=%d"%(stepSize) )
      pass
    if mspl:
      cmd.append( "--mspl=%d"%(mspl) )
      pass
    if amc13local:
      cmd.append( "--amc13local")
      pass
    if t3trig:
      cmd.append( "--t3trig")
      pass
    if randoms > 0:
      cmd.append( "--randoms=%i"%(randoms))
      pass
    if internal:
      cmd.append( "--internal")
      pass
    pass

  #Execute Commands
  try:
    for setupCmd in setupCmds:
      runCommand(setupCmd)
      pass
    log = file("%s/scanLog.log"%(dirPath),"w")
    if preCmd and config:
      runCommand(preCmd,log)
      pass
    runCommand(cmd,log)
  except CalledProcessError as e:
    print "Caught exception",e
    pass
  return

if __name__ == '__main__':

  import sys,os,signal
  import subprocess
  import itertools
  from multiprocessing import Pool, freeze_support
  from gempython.gemplotting.mapping.chamberInfo import chamber_config, chamber_vfatMask
  from gempython.utils.wrappers import envCheck

  from gempython.vfatqc.qcoptions import parser

  parser.add_option("--amc13local", action="store_true", dest="amc13local",
                    help="Set up for using AMC13 local trigger generator", metavar="amc13local")
  parser.add_option("--config", action="store_true", dest="config",
                    help="Configure chambers before running scan", metavar="config")
  parser.add_option("--internal", action="store_true", dest="internal",
                    help="Run a latency scan using the internal calibration pulse", metavar="internal")
  parser.add_option("--perchannel", action="store_true", dest="perchannel",
                    help="Run a per-channel VT1 scan", metavar="perchannel")
  parser.add_option("--randoms", type="int", default=0, dest="randoms",
                    help="Set up for using AMC13 local trigger generator to generate random triggers with rate specified",
                    metavar="randoms")
  parser.add_option("--series", action="store_true", dest="series",
                    help="Run tests in series (default is false)", metavar="series")
  parser.add_option("--stepSize", type="int", dest="stepSize", 
                    help="Supply a step size to the latency scan from scanmin to scanmax", metavar="stepSize", default=1)
  parser.add_option("--t3trig", action="store_true", dest="t3trig",
                    help="Set up for using AMC13 T3 trigger input", metavar="t3trig")
  parser.add_option("--throttle", type="int", default=0, dest="throttle",
                    help="factor by which to throttle the input L1A rate, e.g. new trig rate = L1A rate / throttle", metavar="throttle")
  parser.add_option("--tool", type="string", dest="tool",default="ultraScurve.py",
                    help="Tool to run (scan or analyze", metavar="tool")
  parser.add_option("--trkdata", action="store_true", dest="trkdata",
                    help="Run a per-VFAT VT1 scan using tracking data (default is to use trigger data)", metavar="trkdata")
  parser.add_option("--vt1", type="int", dest="vt1", default=100,
                    help="Specify VT1 to use", metavar="vt1")
  parser.add_option("--vt2", type="int", dest="vt2", default=0,
                    help="Specify VT2 to use", metavar="vt2")

  (options, args) = parser.parse_args()

  envCheck('DATA_PATH')
  envCheck('BUILD_HOME')

  if options.tool not in ["trimChamber.py","ultraThreshold.py","ultraLatency.py","fastLatency.py","ultraScurve.py"]:
    print "Invalid tool specified"
    exit(1)

  if options.debug:
    print list(
            itertools.izip([options.tool for x in range(len(chamber_config))],
                         [options.shelf for x in range(len(chamber_config))],
                         [options.slot for x in range(len(chamber_config))],
                         chamber_config.keys(),
                         chamber_config.values(),
                         [hex(vfatmask) for vfatmask in chamber_vfatMask.values()],
                         [options.scanmin for x in range(len(chamber_config))],
                         [options.scanmax for x in range(len(chamber_config))], 
                         [options.nevts   for x in range(len(chamber_config))],
                         [options.stepSize for x in range(len(chamber_config))],
                         [options.vt1     for x in range(len(chamber_config))],
                         [options.vt2     for x in range(len(chamber_config))],
                         [options.MSPL    for x in range(len(chamber_config))],
                         [options.perchannel for x in range(len(chamber_config))],
                         [options.trkdata for x in range(len(chamber_config))],
                         [options.ztrim   for x in range(len(chamber_config))],
                         [options.config  for x in range(len(chamber_config))],
                         [options.amc13local  for x in range(len(chamber_config))],
                         [options.t3trig  for x in range(len(chamber_config))],
                         [options.randoms for x in range(len(chamber_config))],
                         [options.throttle for x in range(len(chamber_config))],
                         [options.internal for x in range(len(chamber_config))],
                         [options.debug for x in range(len(chamber_config))]
                         )
            )
  if options.series:
    print "Running jobs in serial mode"
    for link in chamber_config.keys():
      chamber = chamber_config[link]
      vfatMask = chamber_vfatMask[link]
      launch([ options.tool,
               options.shelf,
               options.slot,
               link,
               chamber,
               vfatMask,
               options.scanmin,
               options.scanmax,
               options.nevts, 
               options.stepSize,
               options.vt1,
               options.vt2,
               options.MSPL,
               options.perchannel,
               options.trkdata,
               options.ztrim,
               options.config,
               options.amc13local,
               options.t3trig,
               options.randoms,
               options.throttle,
               options.internal,
               options.debug
      ])
      pass
    pass
  else:
    print "Running jobs in parallel mode (using Pool(12))"
    freeze_support()
    # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(12)
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
      res = pool.map_async(launch,
                           itertools.izip([options.tool for x in range(len(chamber_config))],
                                          [options.shelf for x in range(len(chamber_config))],
                                          [options.slot for x in range(len(chamber_config))],
                                          chamber_config.keys(),
                                          chamber_config.values(),
                                          chamber_vfatMask.values(),
                                          [options.scanmin for x in range(len(chamber_config))],
                                          [options.scanmax for x in range(len(chamber_config))],
                                          [options.stepSize for x in range(len(chamber_config))],
                                          [options.nevts   for x in range(len(chamber_config))],
                                          [options.stepSize for x in range(len(chamber_config))],
                                          [options.vt1     for x in range(len(chamber_config))],
                                          [options.vt2     for x in range(len(chamber_config))],
                                          [options.MSPL    for x in range(len(chamber_config))],
                                          [options.perchannel for x in range(len(chamber_config))],
                                          [options.trkdata for x in range(len(chamber_config))],
                                          [options.ztrim   for x in range(len(chamber_config))],
                                          [options.config  for x in range(len(chamber_config))],
                                          [options.amc13local  for x in range(len(chamber_config))],
                                          [options.t3trig  for x in range(len(chamber_config))],
                                          [options.randoms for x in range(len(chamber_config))],
                                          [options.throttle for x in range(len(chamber_config))],
                                          [options.internal for x in range(len(chamber_config))],
                                          [options.debug for x in range(len(chamber_config))]
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
