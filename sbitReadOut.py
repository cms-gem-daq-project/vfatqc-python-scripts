#!/bin/env python

if __name__ == '__main__':
    """
    Script to readout sbits
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="Arguments to supply to sbitReadOut.py")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'", metavar="cardName")
    parser.add_argument("ohN", type=int, help="optohybrid to readout sbits from", metavar="ohN")
    parser.add_argument("acquireTime", type=int, help="time in seconds to acquire sbits for", metavar="acquireTime")
    parser.add_argument("filePath", type=str, help="Filepath where data is stored", metavar="filePath")

    # Optional arguments
    parser.add_argument("--amc13local", action="store_true", dest="amc13local",
            help="Set up for using AMC13 local trigger generator")
    parser.add_argument("--debug", action="store_true", dest="debug",
            help="print additional debugging information")
    parser.add_argument("--fakeTTC", action="store_true", dest="fakeTTC",
            help="Set up for using AMC13 local TTC generator")
    parser.add_argument("--shelf", type=int, dest="shelf",default=1,
            help="uTCA shelf to access", metavar="shelf")
    parser.add_argument("--t3trig", action="store_true", dest="t3trig",
            help="Set up for using AMC13 T3 trigger inpiut")
    parser.add_argument("--vfatmask", type=parseInt, dest="vfatmask",default=0x0,
            help="VFATs to be masked, a 1 in the N^th bit signifies the N^th vfat will not be used", metavar="vfatmask")
    args = parser.parse_args()
    options = vars(args)

    mask = args.vfatmask

    # Open rpc connection to hw
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(args.cardName, args.ohN, args.debug)
    print 'opened connection'

    # Check options
    from gempython.vfatqc.qcutilities import inputOptionsValid
    import os
    if not inputOptionsValid(options, vfatBoard.parentOH.parentAMC.fwVersion):
        exit(os.EX_USAGE)

    # Configure the amc13
    print("initializing amc13")
    import uhal
    if args.debug:
        uhal.setLogLevelTo(uhal.LogLevel.INFO)
    else:
        uhal.setLogLevelTo(uhal.LogLevel.ERROR)
    import amc13
    connection_file = "%s/connections.xml"%(os.getenv("GEM_ADDRESS_TABLE_PATH"))
    amc13base  = "gem.shelf%02d.amc13"%(args.shelf)
    amc13board = amc13.AMC13(connection_file,"%s.T1"%(amc13base),"%s.T2"%(amc13base))

    # Stop triggers from amc13
    print("stopping triggers from amc13 and reseting counters")
    amc13board.enableLocalL1A(False)
    amc13board.resetCounters()
    print("stopping triggers to CTP7")
    vfatBoard.parentOH.parentAMC.blockL1A()
    
    # Get original optohybrid trigger mask and then overwrite it with the vfat mask
    origOhTrigMask = vfatBoard.parentOH.parentAMC.readRegister(
            "GEM_AMC.OH.OH{0}.FPGA.TRIG.CTRL.VFAT_MASK".format(args.ohN),
            args.debug)
    vfatBoard.parentOH.parentAMC.writeRegister(
            "GEM_AMC.OH.OH{0}.FPGA.TRIG.CTRL.VFAT_MASK".format(args.ohN),
            mask,
            args.debug)

    # Configure local triggers?
    if args.amc13local:
        print("configuring the amc13 for local mode")
        #amcMask = amc13board.parseInputEnableList("%s"%(args.slot), True)
        amcMask = amc13board.parseInputEnableList("{0}".format(0xFFF), True)
        amc13board.reset(amc13board.Board.T1)
        amc13board.resetCounters()
        amc13board.resetDAQ()
        if args.fakeTTC:
            print("configuring amc13 for fakeTTC")
            amc13board.localTtcSignalEnable(args.fakeTTC)
        amc13board.AMCInputEnable(amcMask)
        amc13board.startRun()
        if args.t3trig:
            print("configuring the amc13 to use the T3 Trigger input")
            amc13board.write(amc13board.Board.T1, 'CONF.TTC.T3_TRIG', 0x1)
            pass
        # to prevent trigger blocking
        amc13board.fakeDataEnable(True)

    # Place chips in run mode
    print("placing all vfats in run mode")
    vfatBoard.setRunModeAll(mask, True, args.debug)

    # Read chip parameters
    #placeholder

    # Enable triggers
    print("enabling triggers to amc13 and CTP7")
    amc13board.enableLocalL1A(True)
    vfatBoard.parentOH.parentAMC.enableL1A()

    # Readout SBITs
    print("sbitReadOut.py: acquiring sbits")
    vfatBoard.parentOH.parentAMC.acquireSBits(
            args.ohN,
            args.filePath,
            args.acquireTime)
    print("sbitReadOut.py: finished acquiring sbits")

    # Disable triggers
    print("disabling triggers to amc13")
    amc13board.enableLocalL1A(False)
    if args.amc13local:
        amc13board.stopContinuousL1A()
        amc13board.fakeDataEnable(False)

    # Restore original optohybrid trigger mask
    vfatBoard.parentOH.parentAMC.writeRegister(
            "GEM_AMC.OH.OH{0}.FPGA.TRIG.CTRL.VFAT_MASK".format(args.ohN),
            origOhTrigMask,
            args.debug)

    print("Done")
