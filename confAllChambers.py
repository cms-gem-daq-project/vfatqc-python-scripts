#!/bin/env python

import os

def launch(args):
  return launchArgs(*args)

def launchArgs(shelf,slot,link,run,armDAC,armDACBump,configType,cName,debug=False, gemType="ge11"):
    dataPath = os.getenv('DATA_PATH')

    from gempython.vfatqc.utils.qcutilities import getCardName
    from gempython.tools.vfat_user_functions_xhal import HwVFAT
    cardName = getCardName(shelf,slot)
    if gemType == "ge11":
        detType = "short"
    elif gemType == "ge21":
        detType = "m1"
    else:
        print("GEM types other than GE1/1 and GE2/1 aren't supported yet")
        os.exit(1)

    vfatBoard = HwVFAT(cardName, link, debug, gemType, detType)

    from gempython.vfatqc.utils.namespace import Namespace
    args = Namespace(
            applyMasks = False,
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

    from gempython.utils.gemlogger import printYellow
    if (configType & 0x1):          # Set vfatConfig
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
            printYellow("No vfat configuration exists for {0}".format(cName))
    if ( (configType & 0x2) > 0):   # Set chConfig and potentially channel masks
        chConfig = "{0}/configs/chConfig_{1}.txt".format(dataPath,cName)

        if os.path.isfile(chConfig):
            args.chConfig = chConfig
            if ( (configType & 0x4) > 0):
                args.applyMasks = True
        else:
            printYellow("No channel configuration exists for {0}".format(cName))
    if ( (configType & 0x8) > 0):   # Zero all channel registers
        args.chConfig = None
        args.applyMasks = False
        args.zeroChan = True
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
    from gempython.tools.hw_constants import gemVariants
    parser = argparse.ArgumentParser(description="Tool for configuring all front-end electronics")
    parser.add_argument("--armDAC", type=int,default = 100,help="CFG_THR_ARM_DAC value to write to all VFATs")
    parser.add_argument("--armDACBump", type=int,help="CFG_THR_ARM_DAC value for all VFATs", default=0)
    parser.add_argument("-d","--debug", action="store_true",help="prints additional debugging information")
    parser.add_argument("--run", action="store_true",help="Set VFATs to run mode")
    parser.add_argument("--series", action="store_true",help="Run tests in series (default is false)")
    parser.add_argument("--shelf", type=int,help="uTCA shelf number",default=1)
    parser.add_argument("--gemType",type=str,help="String that defines the GEM variant, available from the list: {0}".format(gemVariants.keys()),default="ge11")

    confGroup = parser.add_argument_group(title="Configuration Group",description="Options for configuring channel registers and CFG_THR_ARM_DAC")
    confGroup.add_argument("--applyMasks", action="store_true",help="If paired with --chConfig channel masks defined in chConfig text file will be applied; otherwise no effect")
    confGroup.add_argument("--vfatConfig", action="store_true",help="Set only CFG_THR_ARM_DAC registers from symlinks found under $DATA_PATH/configs")
    chConfGroup = confGroup.add_mutually_exclusive_group()
    chConfGroup.add_argument("--chConfig", action="store_true",help="Set only channel registers from symlinks found under $DATA_PATH/configs")
    chConfGroup.add_argument("--zeroChan", action="store_true",help="Zeros all channel registers")
    args = parser.parse_args()

    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')

    # determine configType, 4-bit number with bit meaning as:
    # [0] -> apply vfatConfig
    # [1] -> apply chConfig
    # [2] -> apply channel masks
    # [3] -> zero channels
    configType=0x0
    if args.vfatConfig:
        configType |= 0x1
    if args.chConfig:
        configType |= 0x2
        if args.applyMasks:
            configType |= 0x4
    if args.zeroChan:
        configType |= 0x8
        pass

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
                        [ohKey[0]                   for ohKey in chambers2Configure],
                        [ohKey[1]                   for ohKey in chambers2Configure],
                        [ohKey[2]                   for ohKey in chambers2Configure],
                        [args.run                   for ohKey in chambers2Configure],
                        [args.armDAC                for ohKey in chambers2Configure],
                        [args.armDACBump            for ohKey in chambers2Configure],
                        [configType                 for ohKey in chambers2Configure],
                        [chambers2Configure[ohKey]  for ohKey in chambers2Configure.keys()],
                        [args.debug                 for ohKey in chambers2Configure.keys()]
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
                    configType,
                    chamber,
                    args.debug,
                    args.gemType
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
                                    [configType                for ohKey in chambers2Configure],
                                    [chambers2Configure[ohKey] for ohKey in chambers2Configure.keys()],
                                    [args.debug                for ohKey in chambers2Configure.keys()],
                                    [args.gemType              for ohKey in chambers2Configure.keys()]
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
