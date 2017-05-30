#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(link,slot,run,vt1,vt1bump,config,cName,ztrim):
    import datetime,os,sys
    import subprocess
    from subprocess import CalledProcessError
    from chamberInfo import chamber_config
    from gempython.utils.wrappers import runCommand

    dataPath = os.getenv('DATA_PATH')
    filename="%s/%s/trim/z%f/config/SCurveData_Trimmed/SCurveFitData.root"%(dataPath,cName,options.ztrim)

    if not os.path.isfile(filename):
        print "No trim configuration exists for z = %f for %s"%(ztrim,cName)
        return

    cmd = ["confChamber.py","-s%d"%(slot),"-g%d"%(link)]

    if run:
        cmd.append("--run")
        pass

    if config:
        cmd.append("--vfatConfig=%s/configs/z%.1f/vfatConfig_%s.txt"%(dataPath,ztrim,cName))
        cmd.append("--chConfig=%s/configs/z%.1f/chConfig_%s.txt"%(dataPath,ztrim,cName))
    else:
        cmd.append("--vt1=%d"%(vt1))
        cmd.append("--vt1bump=%d"%(vt1bump))
        cmd.append("--filename=%s"%(filename))  
        pass

    try:
        runCommand(cmd)
    except CalledProcessError as e:
        print "Caught exception",e
        pass
    return


if __name__ == '__main__':

    import sys,os,signal
    import subprocess
    import itertools
    from multiprocessing import Pool, freeze_support
    from chamberInfo import chamber_config
    from gempython.utils.wrappers import envCheck

    from qcoptions import parser

    parser.add_option("--run", action="store_true", dest="run",
                      help="Set VFATs to run mode", metavar="run")
    parser.add_option("--config", action="store_true", dest="config",
                      help="Set Configuration from simple txt files", metavar="config")
    parser.add_option("--vt1", type="int", dest="vt1",
                      help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)
    parser.add_option("--vt1bump", type="int", dest="vt1bump",
                      help="VThreshold1 DAC bump value for all VFATs", metavar="vt1bump", default=0)

    (options, args) = parser.parse_args()

    envCheck('DATA_PATH')

    freeze_support()
    # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(12)
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
        res = pool.map_async(launch,
                             itertools.izip(chamber_config.keys(),
                                            [options.slot      for x in range(len(chamber_config))],
                                            [options.run       for x in range(len(chamber_config))],
                                            [options.vt1       for x in range(len(chamber_config))],
                                            [options.vt1bump   for x in range(len(chamber_config))],
                                            [options.config    for x in range(len(chamber_config))],
                                            [chamber_config[x] for x in chamber_config.keys()],
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
