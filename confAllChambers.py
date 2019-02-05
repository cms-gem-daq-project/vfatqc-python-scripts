#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(shelf,link,slot,run,vt1,vt1bump,config,cName,debug=False):
    import os, logging
    from subprocess import CalledProcessError
    from gempython.utils.wrappers import runCommand
    from gempython.gemplotting.mapping.chamberInfo import chamber_vfatMask

    dataPath = os.getenv('DATA_PATH')
    filename="%s/%s/trim/config/SCurveData_Trimmed/SCurveFitData.root"%(dataPath,cName)

    cardName = "--cardName=gem-shelf%02d-amc%02d"%(shelf,slot)
    cmd = ["confChamber.py",cardName,"-g%d"%(link),]

    if debug:
        cmd.append("--debug")
        pass

    if run:
        cmd.append("--run")
        pass

    if link in chamber_vfatMask:
        cmd.append("--vfatmask={0}".format(str(hex(chamber_vfatMask[link])).strip('L')))

    if config:
        cmd.append("--vt1bump=%d"%(vt1bump))
        chConfig = "{0}/configs/vfatConfig_{1}.txt".format(dataPath,cName)
        vfatConfig = "{0}/configs/vfatConfig_{1}.txt".format(dataPath,cName)
        
        # Channel config
        if os.path.isfile(chConfig):
            cmd.append("--chConfig={}".format(chConfig))
        else:
            print("No channel configuration exists for {0}".format(cName))
        
        # VFAT Config
        if os.path.isfile(vfatConfig):
            cmd.append("--vfatConfig={}".format(vfatConfig))
        else:
            print("No vfat configuration exists for {0}".format(cName))

        pass
    else:
        if os.path.isfile(filename):
            cmd.append("--filename=%s"%(filename))
        else:
            print "No trim configuration exists for %s"%(cName)
        pass
    cmd.append("--vt1=%d"%(vt1))

    from gempython.utils.gemlogger import getGEMLogger
    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.ERROR)
    #setAMCLogLevel(logging.ERROR)
    #setOHLogLevel(logging.ERROR)
    
    #uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    try:
        runCommand(cmd)
    except CalledProcessError as e:
        print "Caught exception",e
        pass
    return

if __name__ == '__main__':
    import sys,signal
    import itertools
    from multiprocessing import Pool, freeze_support
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    from gempython.utils.wrappers import envCheck

    #from gempython.vfatqc.utils.qcoptions import parser
    from gempython.utils.standardopts import parser
    parser.add_option("--config", action="store_true", dest="config",
                      help="Set Configuration from simple txt files", metavar="config")
    parser.add_option("--run", action="store_true", dest="run",
                      help="Set VFATs to run mode", metavar="run")
    parser.add_option("--series", action="store_true", dest="series",
                      help="Run tests in series (default is false)", metavar="series")
    parser.add_option("--vt1", type="int", dest="vt1",
                      help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)
    parser.add_option("--vt1bump", type="int", dest="vt1bump",
                      help="VThreshold1 DAC bump value for all VFATs", metavar="vt1bump", default=0)
    parser.add_option("--ztrim", type="float", dest="ztrim", default=4.0,
                      help="Specify the p value of the trim", metavar="ztrim")
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
                        [options.debug     for x in range(len(chamber_config))]
                  )
            )
        pass
    if options.series:
        print "Configuring chambers in serial mode"
        for link in chamber_config.keys():
            chamber = chamber_config[link]
            launchArgs(options.shelf,link,options.slot,options.run,options.vt1,options.vt1bump,options.config,chamber,options.debug)
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
                                                [options.debug     for x in range(len(chamber_config))]
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
