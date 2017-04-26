#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(link,scandate,cName,cType,ztrim):
    import datetime,os,sys
    import subprocess
    from subprocess import CalledProcessError
    from chamberInfo import chamber_config
    from gempython.utils.wrappers import runCommand

    filename = "/gemdata/%s/scurve/%s/SCurveData.root"%(cName,scandate)
    if not os.path.isfile(filename):
        print "No file to analyze. %s does not exist"%(filename)
        return


    cmd1 = ["python","$BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py"]
    cmd1.append("--infilename=%s"%(filename))
    cmd1.append("--fit", "--type=%s"%(cType))

    cmd2 = ["cp","/gemdata/%s/scurve/%s/SCurveData/Summary.png"%(cName,scandate),
            "~/move/SCurveSummary_%s_ztrip%2.2f.png"%(cName,ztrim)]

    try:
        runCommand(cmd1)
        runCommand(cmd2)
    except CalledProcessError as e:
        print "Caught exception",e
        pass
    return


if __name__ == '__main__':

    from chamberInfo import chamber_config,GEBtype
    from qcoptions import parser

    parser.add_option("--scandate", type="string", dest="scandate", default="current",
                      help="Specify specific date to analyze", metavar="scandate")

    (options, args) = parser.parse_args()

    ztrim = options.ztrim

    import glob

    envCheck('DATA_PATH')
    searchPath = "%s/GEMINI*/scurve/*"%(os.getenv('DATA_PATH'))
    dirs       = glob.glob(searchPath)
    foundDir   = False

    for path in dirs:
        if path.rfind(options.scandate) > 0:
            foundDir = True
    if not foundDir:
        print "Unable to find %s in output location specified: %s"%(options.scandate,searchPath)
        exit(50)
    else:
        print "Found %s"%(options.scandate)


    freeze_support()
    # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(12)
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
        res = pool.map_async(launch,
                             itertools.izip(chamber_config.keys(),
                                            [options.scandate  for x in range(len(chamber_config))],
                                            [chamber_config[x] for x in chamber_config.keys()],
                                            [GEBtype[x]        for x in chamber_config.keys()],
                                            [options.ztrim     for x in range(len(chamber_config))],
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
