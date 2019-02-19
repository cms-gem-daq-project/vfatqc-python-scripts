#!/bin/env python
from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize

import os

def printDACOptions():
    print("dac\tName")
    print("===\t====")
    dacOptions = maxVfat3DACSize.keys()
    dacOptions.sort()
    for dacVal in dacOptions:
        print("%02d\t%s"%(dacVal,maxVfat3DACSize[dacVal][1]))
    return

if __name__ == '__main__':
    """
    Script to perform DAC scans with VFAT3
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="Scans a given DAC on a VFAT3 against the chip's ADC.  Either the internally or externally referenced ADC can be used.  Scans all VFATs on a given link simultaneously")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'; if running on an AMC use 'local' instead", metavar="cardName")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    # Optional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            help = "Print additional debugging information")
    parser.add_argument("--dacSelect", type=int, dest="dacSelect",
            help = "DAC Selection", default=None)
    parser.add_argument("-e","--extRefADC", action="store_true", dest="extRefADC",
            help = "Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-f","--filename",type=str,dest="filename",default="dacScanV3.root",
            help = "Specify output filename to store data in.")
    parser.add_argument("--series", action="store_true", dest="series",
            help = "Scan nonzero links in ohMask in series (successive RPC calls) instead of in parallel (one RPC call)")
    parser.add_argument("--stepSize", type=int, dest="stepSize",default=1, 
                  help="Supply a step size for the scan")
    parser.add_argument("-v","--vfatmask",type=parseInt,dest="vfatmask",default=None,
            help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFF masks all VFATs)")
    args = parser.parse_args()

    if args.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    if ((args.dacSelect not in maxVfat3DACSize.keys()) and (args.dacSelect is not None)):
        print("Input DAC selection {0} not understood".format(args.dacSelect))
        print("possible options include:")
        printDACOptions()
        exit(os.EX_USAGE)

    # Open rpc connection to hw
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(args.cardName, 0, args.debug) # Assign link 0; we will update later
    print 'opened connection'
    amcBoard = vfatBoard.parentOH.parentAMC
    if amcBoard.fwVersion < 3:
        print("DAC Scan of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)
    
    # Check options
    from gempython.vfatqc.utils.qcutilities import inputOptionsValid
    if not inputOptionsValid(args, amcBoard.fwVersion):
        exit(os.EX_USAGE)
        pass
    
    # Make output files
    import ROOT as r
    outF = r.TFile(args.filename,"RECREATE")
    from gempython.vfatqc.utils.scanUtils import dacScanAllLinks, dacScanSingleLink 
    from gempython.vfatqc.utils.treeStructure import gemDacCalTreeStructure
    calTree = gemDacCalTreeStructure(
                    name="dacScanTree",
                    nameX="dummy", # temporary name, will be over-ridden
                    nameY=("ADC1" if args.extRefADC else "ADC0"),
                    dacSelect=-1, #temporary value, will be over-ridden 
                    description="GEM DAC Calibration of VFAT3 DAC"
            )

    if args.dacSelect is None: # No DAC selected; scan them all
        for dacSelect in maxVfat3DACSize.keys():
            args.dacSelect = dacSelect
            if args.series:
                for ohN in range(0, amcBoard.nOHs+1):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue

                    # update the OH in question
                    vfatBoard.parentOH.link = ohN

                    dacScanSingleLink(args, calTree, vfatBoard)
                    pass
                pass
            else:
                dacScanAllLinks(args, calTree, vfatBoard)
    else: # Specific DAC Requested; scan only this DAC
        if args.series:
            for ohN in range(0, amcBoard.nOHs+1):
                if( not ((args.ohMask >> ohN) & 0x1)):
                    continue

                # update the OH in question
                vfatBoard.parentOH.link = ohN

                dacScanSingleLink(args, calTree, vfatBoard)
                pass
            pass
        else:
            dacScanAllLinks(args, calTree, vfatBoard)

    outF.cd()
    calTree.autoSave("SaveSelf")
    calTree.write()
    outF.Close()

    print("All DAC Scans Completed. Goodbye")
