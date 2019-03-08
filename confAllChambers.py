#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(shelf,slot,link,run,armDAC,armDACBump,config,cName,debug=False):
    import os
    dataPath = os.getenv('DATA_PATH')

    from gempython.vfatqc.utils.qcutilities import getCardName
    from gempython.tools.vfat_user_functions_xhal import HwVFAT
    cardName = getCardName(shelf,slot)
    vfatBoard = HwVFAT(cardName, link, debug)

    from gempython.vfatqc.utils.namespace import Namespace
    args = Namespace(
            debug = debug,
            run = run,
            vt1 = armDAC,
            vt1bump = armDACBump,
            vfatmask = vfatBoard.parentOH.getVFATMask()
            )

    if config:
        chConfig = "{0}/configs/chConfig_{1}.txt".format(dataPath,cName)
        vfatConfig = "{0}/configs/vfatConfig_{1}.txt".format(dataPath,cName)

        # Channel config
        if os.path.isfile(chConfig):
            args.chConfig = chConfig
        else:
            print("No channel configuration exists for {0}".format(cName))
        
        # VFAT Config
        if os.path.isfile(vfatConfig):
            args.vfatConfig = vfatConfig
        else:
            print("No vfat configuration exists for {0}".format(cName))

        pass

    from gempython.utils.gemlogger import getGEMLogger
    import logging
    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.ERROR)

    from gempython.vfatqc.utils.confUtils import configure
    from subprocess import CalledProcessError
    try:
        configure(args,vfatBoard)
    except CalledProcessError as e:
        print "Caught exception",e
        pass
    return

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description="Tool for configuring all front-end electronics")
    parser.add_argument("--armDAC", type=int, dest = "armDAC", default = 100,
                      help="CFG_THR_ARM_DAC value to write to all VFATs", metavar="armDAC")
    parser.add_argument("--armDACBump", type=int, dest="armDACBump",
                      help="CFG_THR_ARM_DAC value for all VFATs", metavar="armDACBump", default=0)
    parser.add_argument("--config", action="store_true", dest="config",
                      help="Set Configuration from simple txt files", metavar="config")
    parser.add_argument("--run", action="store_true", dest="run",
                      help="Set VFATs to run mode", metavar="run")
    parser.add_argument("--series", action="store_true", dest="series",
                      help="Run tests in series (default is false)", metavar="series")
    (options, args) = parser.parse_args()

    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')

    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    import itertools
    if options.debug:
        print list(itertools.izip(
                        [ohKey[0]              for ohKey in chamber_config],
                        [ohKey[1]              for ohKey in chamber_config],
                        [ohKey[2]              for ohKey in chamber_config],
                        [options.run           for ohKey in chamber_config],
                        [options.armDAC        for ohKey in chamber_config],
                        [options.armDACBump    for ohKey in chamber_config],
                        [options.config        for ohKey in chamber_config],
                        [chamber_config[ohKey] for ohKey in chamber_config.keys()],
                        [options.debug         for ohKey in chamber_config.keys()]
                  )
            )
        pass
    if options.series:
        print "Configuring chambers in serial mode"
        for ohKey in chamber_config.keys():
            chamber = chamber_config[ohKey]
            launchArgs(
                    ohKey[0],
                    ohKey[1],
                    ohKey[2],
                    options.run,
                    options.armDAC,
                    options.armDACBump,
                    options.config,
                    chamber,
                    options.debug
                    )
            pass
        pass
    else:
        from multiprocessing import Pool, freeze_support
        freeze_support()
        # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool(12)
        
        import sys,signal
        signal.signal(signal.SIGINT, original_sigint_handler)
        try:
            res = pool.map_async(launch,
                                 itertools.izip(
                                    [ohKey[0]              for ohKey in chamber_config],
                                    [ohKey[1]              for ohKey in chamber_config],
                                    [ohKey[2]              for ohKey in chamber_config],
                                    [options.run           for ohKey in chamber_config],
                                    [options.armDAC        for ohKey in chamber_config],
                                    [options.armDACBump    for ohKey in chamber_config],
                                    [options.config        for ohKey in chamber_config],
                                    [chamber_config[ohKey] for ohKey in chamber_config.keys()],
                                    [options.debug         for ohKey in chamber_config.keys()]
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
