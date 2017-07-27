#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(shelf,link,slot,run,vt1,vt1bump,config,dictConfig,cName,ztrim):
    import datetime,os,sys
    import subprocess
    from subprocess import CalledProcessError
    from chamberInfo import chamber_config
    from gempython.utils.wrappers import runCommand

    dataPath = os.getenv('DATA_PATH')
    filename="%s/%s/trim/z%f/config/SCurveData_Trimmed/SCurveFitData.root"%(dataPath,cName,options.ztrim)

    cmd = ["confChamber.py","-s%d"%(slot),"-g%d"%(link),"--shelf=%i"%(shelf)]

    if run:
        cmd.append("--run")
        pass

    if config:
        cmd.append("--vt1bump=%d"%(vt1bump))
        if options.dictConfig:
            cmd.append("--dictConfig")
            pass
        else:
            cmd.append("--vfatConfig=%s/configs/z%.1f/vfatConfig_%s.txt"%(dataPath,ztrim,cName))
            pass
        cmd.append("--chConfig=%s/configs/z%.1f/chConfig_%s.txt"%(dataPath,ztrim,cName))
        pass
    else:
        if not os.path.isfile(filename):
            print "No trim configuration exists for z = %f for %s"%(ztrim,cName)
            return
        cmd.append("--filename=%s"%(filename))  
        pass
    cmd.append("--vt1=%d"%(vt1))

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

    parser.add_option("--config", action="store_true", dest="config",
                      help="Set Configuration from simple txt files", metavar="config")
    parser.add_option("--dictConfig", action="store_true", dest="dictConfig", default=False,
                      help="Configure VFATs to custom chamber_default values", metavar="dictConfig")
    parser.add_option("--run", action="store_true", dest="run",
                      help="Set VFATs to run mode", metavar="run")
    parser.add_option("--series", action="store_true", dest="series",
                      help="Run tests in series (default is false)", metavar="series")
    parser.add_option("--vt1", type="int", dest="vt1",
                      help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)
    parser.add_option("--vt1bump", type="int", dest="vt1bump",
                      help="VThreshold1 DAC bump value for all VFATs", metavar="vt1bump", default=0)

    (options, args) = parser.parse_args()

    envCheck('DATA_PATH')
  
    if options.debug:
        print list(itertools.izip(
                        [options.shelf     for x in range(len(chamber_config))],
                        chamber_config.keys(),
                        [options.slot      for x in range(len(chamber_config))],
                        [options.run       for x in range(len(chamber_config))],
                        [options.vt1       for x in range(len(chamber_config))],
                        [options.vt1bump   for x in range(len(chamber_config))],
                        [options.config    for x in range(len(chamber_config))],
                        [chamber_config[x] for x in chamber_config.keys()],
                        [options.dictConfig for x in range(len(chamber_config))],
                        [options.ztrim     for x in range(len(chamber_config))],
                  )
            )
        pass
    if options.series:
        print "Configuring chambers in serial mode"
        for link in chamber_config.keys():
            chamber = chamber_config[link]
            launchArgs(options.shelf,link,options.slot,options.run,options.vt1,options.vt1bump,options.config,options.dictConfig,chamber,options.ztrim)
            pass
        pass
    else:
        freeze_support()
        # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool(12)
        signal.signal(signal.SIGINT, original_sigint_handler)
        try:
            res = pool.map_async(launch,
                                 itertools.izip([options.shelf     for x in range(len(chamber_config))],
                                                chamber_config.keys(),
                                                [options.slot      for x in range(len(chamber_config))],
                                                [options.run       for x in range(len(chamber_config))],
                                                [options.vt1       for x in range(len(chamber_config))],
                                                [options.vt1bump   for x in range(len(chamber_config))],
                                                [options.config    for x in range(len(chamber_config))],
                                                [chamber_config[x] for x in chamber_config.keys()],
                                                [options.dictConfig  for x in range(len(chamber_config))],
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
