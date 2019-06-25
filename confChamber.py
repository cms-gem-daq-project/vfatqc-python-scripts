#!/bin/env python

if __name__ == '__main__':
    """
    Script to configure the VFATs on a GEM chamber
    By: Cameron Bravo c.bravo@cern.ch
    Modified by: Eklavya Sarkar eklavya.sarkar@cern.ch
                 Brian Dorney brian.l.dorney@cern.ch
    """

    from array import array
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.vfatqc.utils.qcutilities import getCardName, inputOptionsValid
    from gempython.vfatqc.utils.confUtils import configure, readBackCheckV3, setChannelRegisters

    import argparse
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser = argparse.ArgumentParser(description="Tool for configuring front-end electronics")

    parser.add_argument("--applyMasks", action="store_true", help="Channel masks defined in chConfig will be applied if this option is provided; otherwise no channel masks will be set")
    parser.add_argument("--chConfig", type=str, dest="chConfig", default=None,
                      help="Specify file containing channel settings from anaUltraSCurve.py")
    parser.add_argument("--compare", action="store_true", dest="compare",
                      help="When supplied with {chConfig, filename, vfatConfig} compares current reg values with those stored in input files")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug",
                      help="print extra debugging information")
    parser.add_argument("--filename", type=str, dest="filename", default=None,
                      help="Specify file containing settings information")
    parser.add_argument("-g", "--gtx", type=int, dest="gtx",
                      help="GTX on the AMC", default=0)
    parser.add_argument("--mspl", type=int, dest = "MSPL", default = 3,
                      help="Specify CFG_PULSE_STRETCH. Must be in the range 0-7 (default is 3)")
    parser.add_argument("--run", action="store_true", dest="run",
                      help="Set VFATs to run mode")
    parser.add_argument("--shelf", type=int, dest="shelf",default=1,
                	  help="uTCA shelf to access")
    parser.add_argument("-s","--slot", type=int, dest="slot",default=4,
                      help="slot in the uTCA of the AMC you are connceting too")
    parser.add_argument("--vfatConfig", type=str, dest="vfatConfig", default=None,
                      help="Specify file containing VFAT settings from anaUltraThreshold.py or anaSBitThresh.py")
    parser.add_argument("--vfatmask", type=parseInt, dest="vfatmask",
                      help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFFF masks all VFATs)", default=0x0)
    parser.add_argument("--vt1", type=int, dest="vt1",
                      help="VThreshold1 or CFG_THR_ARM_DAC value for all VFATs", default=100)
    parser.add_argument("--vt2", type=int, dest="vt2",
                      help="VThreshold2 DAC value for all VFATs (v2b electronics only)", default=0)
    parser.add_argument("--vt1bump", type=int, dest="vt1bump",
                      help="VThreshold1 DAC bump value for all VFATs", default=0)
    parser.add_argument("--zeroChan", action="store_true", dest="zeroChan",
                      help="Zero all channel registers")
    parser.add_argument("--gemType",type=str,help="String that defines the GEM variant, available from the list: {0}".format(gemVariants.keys()),default="ge11")
    parser.add_argument("--detType",type=str,help="Detector type within gemType. If gemType is 'ge11' then this should be from list {0}; if gemType is 'ge21' then this should be from list {1}; and if type is 'me0' then this should be from the list {2}".format(gemVariants['ge11'],gemVariants['ge21'],gemVariants['me0']),default=None)
    args = parser.parse_args()

    import subprocess,datetime
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print startTime
    Date = startTime

    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName, link=args.gtx, debug=args.debug, gemType=args.gemType, detType=args.detType)
    print('opened connection')

    # Check args
    if not inputOptionsValid(args, vfatBoard.parentOH.parentAMC.fwVersion):
        print("input options are not valid, exiting")
        exit(os.EX_USAGE)
        pass

    configure(args,vfatBoard)

    print 'Chamber Configured'
