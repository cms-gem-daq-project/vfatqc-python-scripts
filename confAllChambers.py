#!/bin/env python

import os

def launch(args):
  return launchArgs(*args)

def launchArgs(shelf,slot,link,run,armDAC,armDACBump,config,cName,debug=False):
    dataPath = os.getenv('DATA_PATH')

    from gempython.vfatqc.utils.qcutilities import getCardName
    from gempython.tools.vfat_user_functions_xhal import HwVFAT
    cardName = getCardName(shelf,slot)
    vfatBoard = HwVFAT(cardName, link, debug)

    from gempython.vfatqc.utils.namespace import Namespace
    args = Namespace(
            chConfig = None,
            compare = False,
            debug = debug,
            filename = None,
            run = run,
            vt1 = armDAC,
            vt1bump = armDACBump,
            vt2 = 0,
            vfatConfig = None,
            vfatmask = vfatBoard.parentOH.getVFATMask(),
            zeroChan = False
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
    parser.add_argument("--armDAC", type=int,default = 100,help="CFG_THR_ARM_DAC value to write to all VFATs")
    parser.add_argument("--armDACBump", type=int,help="CFG_THR_ARM_DAC value for all VFATs", default=0)
    parser.add_argument("--config", action="store_true",help="Set Configuration from simple txt files")
    parser.add_argument("-d","--debug", action="store_true",help="prints additional debugging information")
    parser.add_argument("--run", action="store_true",help="Set VFATs to run mode")
    parser.add_argument("--series", action="store_true",help="Run tests in series (default is false)")
    parser.add_argument("--shelf", type=int,help="uTCA shelf number",default=1)
    args = parser.parse_args()

    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')

    # consider only the shelf of interest
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    chambers2Configure = {}
    for ohKey,cName in chamber_config.iteritems():
        if args.shelf == ohKey[0]:
            chambers2Configure[ohKey] = cName
            pass
        pass
    
    from gempython.utils.gemlogger import printRed
    if (len(chambers2Configure) == 0):
        printRed("No chambers for shelf{0} exist".format(args.shelf))
        printRed("Nothing to do, exiting")
        exit(os.EX_USAGE)

    import itertools
    if args.debug:
        print list(itertools.izip(
                        [ohKey[0]                  for ohKey in chambers2Configure],
                        [ohKey[1]                  for ohKey in chambers2Configure],
                        [ohKey[2]                  for ohKey in chambers2Configure],
                        [args.run                  for ohKey in chambers2Configure],
                        [args.armDAC               for ohKey in chambers2Configure],
                        [args.armDACBump           for ohKey in chambers2Configure],
                        [args.config               for ohKey in chambers2Configure],
                        [chambers2Configure[ohKey] for ohKey in chambers2Configure.keys()],
                        [args.debug                for ohKey in chambers2Configure.keys()]
                  )
            )
        pass
    if args.series:
        print "Configuring chambers in serial mode"
        for ohKey in chambers2Configure.keys():
            chamber = chambers2Configure[ohKey]
            launchArgs(
                    ohKey[0],
                    ohKey[1],
                    ohKey[2],
                    args.run,
                    args.armDAC,
                    args.armDACBump,
                    args.config,
                    chamber,
                    args.debug
                    )
            pass
        pass
    else:
        from multiprocessing import Pool, freeze_support
        import sys,signal
        freeze_support()
        # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = Pool(12)
        
        signal.signal(signal.SIGINT, original_sigint_handler)
        try:
            res = pool.map_async(launch,
                                 itertools.izip(
                                    [ohKey[0]                  for ohKey in chambers2Configure],
                                    [ohKey[1]                  for ohKey in chambers2Configure],
                                    [ohKey[2]                  for ohKey in chambers2Configure],
                                    [args.run                  for ohKey in chambers2Configure],
                                    [args.armDAC               for ohKey in chambers2Configure],
                                    [args.armDACBump           for ohKey in chambers2Configure],
                                    [args.config               for ohKey in chambers2Configure],
                                    [chambers2Configure[ohKey] for ohKey in chambers2Configure.keys()],
                                    [args.debug                for ohKey in chambers2Configure.keys()]
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
