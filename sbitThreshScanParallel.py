#!/bin/env python

if __name__ == '__main__':
    """
    Script to measure sbit rate as a function of CFG_THR_ARM_DAC
    By: Brian Dorney (brian.l.dorney@cern.ch)
        Evaldas Juska (evaldas.juska@cern.ch)
    """
    
    import sys, os
    from array import array
    from ctypes import *
    
    from gempython.tools.vfat_user_functions_xhal import *
    
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="For each unmasked optohybrid this script will scan the CFG_THR_ARM_DAC register for each VFAT on the optohybrid. At each DAC point it will measure the rate of SBITs being sent to the optohybrid.  All links will be measured simultaneously.")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("shelf", type=int, help="uTCA shelf to access")
    parser.add_argument("slot", type=int,help="slot in the uTCA of the AMC you are connceting too")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered")
    
    # Optional arguments
    parser.add_argument("--chMin", type=int, help="Specify minimum channel number to scan", default=0)
    parser.add_argument("--chMax", type=int, help="Specify maximum channel number to scan", default=127)
    parser.add_argument("-d", "--debug", action="store_true", help="print extra debugging information")
    parser.add_argument("-f", "--filename", type=str, help="Specify Output Filename", default="SBitRateData.root")
    parser.add_argument("--perchannel", action="store_true", help="Run a per-channel sbit rate scan")
    parser.add_argument("--scanmin", type=int, help="Minimum value of scan parameter", default=0)
    parser.add_argument("--scanmax", type=int, help="Maximum value of scan parameter", default=255)
    parser.add_argument("--stepSize", type=int, help="Supply a step size to the scan from scanmin to scanmax", default=1)
    args = parser.parse_args()
    
    from gempython.utils.gemlogger import printRed, printYellow
    remainder = (args.scanmax-args.scanmin+1) % args.stepSize
    if remainder != 0:
        args.scanmax = args.scanmax - remainder
        printYellow("Reducing scanmax to: {0}".format(args.scanmax))
   
    if args.scanmax > 255:
        printYellow("CFG_THR_ARM_DAC and CFG_THR_ZCC_DAC only go up to 0xff (255)")
        printYellow("Current value %i will roll over to 0"%(args.scanmax))
        printYellow("Seting scanmax to 255")
        args.scanmax=255
    
    #determine total time in hours
    if args.perchannel:
        totalTime=(args.scanmax-args.scanmin)*(args.chMax-args.chMin)*(1./3600.)
        
        print("I see you've asked for a perchannel scan")
        print("Right now this is done in series, are you sure you want to continue?")
        print("I expect this will take: %f hours"%totalTime)
        
        bInputUnderstood=False
        performTest=raw_input("Do you want to continue? (yes/no)")
        while(not bInputUnderstood):
            performTest=performTest.upper()
            if performTest == "NO":
                print("Okay, exiting!")
                print("Please run again and change the '--chMin', '--chMax', '--scanmin', and/or '--scanmax' parameters")
                sys.exit(os.EX_USAGE)
            elif performTest == "YES":
                bInputUnderstood = True
                break;
            else:
                performTest=raw_input("input not understood, please enter 'yes' or 'no'")

    # Open rpc connection to hw
    from gempython.vfatqc.utils.qcutilities import getCardName, inputOptionsValid
    cardName = getCardName(args.shelf,args.slot)
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(cardName, 0, args.debug) # Assign link 0; we will update later
    print 'opened connection'
    amcBoard = vfatBoard.parentOH.parentAMC
    if amcBoard.fwVersion < 3:
        print("SBIT Threshold Scan of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)

    # Check options
    if not inputOptionsValid(args, amcBoard.fwVersion):
        exit(os.EX_USAGE)
        pass

    # Make output files
    import ROOT as r
    outF = r.TFile(args.filename,'recreate')
    from gempython.vfatqc.utils.treeStructure import gemSbitRateTreeStructure
    rateTree = gemSbitRateTreeStructure(nameX="CFG_THR_ARM_DAC")
    
    import time
    rateTree.utime[0] = int(time.time())

    # Scan over all channels or just a channel OR???
    from gempython.vfatqc.utils.scanUtils import sbitRateScanAllLinks
    if args.perchannel:
        for chan in range(args.chMin,args.chMax+1):
            sbitRateScanAllLinks(args,rateTree,vfatBoard,chan=chan)
            pass
        pass
    else:
        sbitRateScanAllLinks(args,rateTree,vfatBoard)
        pass

    outF.cd()
    rateTree.autoSave("SaveSelf")
    rateTree.write()
    outF.Close()

    print("Scan Completed. Goodbye!")
