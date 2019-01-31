#!/bin/env python

from gempython.tools.vfat_user_functions_xhal import *
from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
from gempython.utils.gemlogger import printGreen, printRed, printYellow

def testConnectivity(args):
    # Check if cardName is in args
    if hasattr(args, 'cardName') is False:
        args.cardName = "gem-shelf%02d-amc%02d"%(args.shelf,args.slot)

    # Initialize Hardware
    amc = getAMCObject(args.slot,args.shelf)
    nOHs = readRegister(amc,"GEM_AMC.GEM_SYSTEM.CONFIG.NUM_OF_OH")
    
    vfatBoard = HwVFAT(args.cardName,0) # assign a dummy link for now

    # Check GBT Communication
    # =================================================================

    # Check SCA Communication
    # =================================================================
    printYellow("="*20)
    printYellow("Checking SCA Communication")
    printYellow("="*20)

    scaCommPassed = False
    from reg_utils.reg_interface.scripts.sca import scaReset
    for trial in range(0,args.maxIter):
        scaReset(args)
        scaInfo = printSystemSCAInfo(amc)

        if scaInfo["READY"] != args.ohMask:
            continue
        if scaInfo["CRITICAL_ERROR"] != 0x0:
            continue
        
        notRdyCntOkay = True
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            if scaInfo["NOT_READY_CNT"][ohN] != 0x2:
                notRdyCntOkay = False
                break
            pass
        if not notRdyCntOkay:
            continue
        
        # reaching here passes all tests for this stage
        scaCommPassed = True
        break

    if not scaCommPassed:
        printRed("SCA Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. OH3 screw is properly screwed into standoff")
        printYellow("\t\t2. OH3 standoff on the GEB is not broken")
        printYellow("\t\t3. Voltage on OH3 standoff is within range [X,Y] Volts")
        printRed("Connectivity Testing Failed")
        return
    else: 
        printGreen("SCA Communication Established")
        pass

    # Program FPGA
    # =================================================================
    vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.TTC.GENERATOR.ENABLE",0x1)

    fpgaCommPassed = False
    for trial in range(0,args.maxIter):
        vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.TTC.GENERATOR.SINGLE_HARD_RESET",0x1)
        isDead = True
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            fwVerMaj = vfatBoard.parentOH.parentAMC.readRegister("GEM_AMC.OH.OH{0}.FPGA.CONTROL.RELEASE.VERSION.MAJOR".format(ohN))
            if fwVerMaj != 0xdeaddead:
                isDead = False
            else:
                isDead = True
                pass
            pass

        if not isDead:
            fpgaCommPassed = True
            break
        pass

    vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.TTC.GENERATOR.ENABLE",0x0)
    
    if not fpgaCommPassed:
        printRed("FPGA Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Was the OH FW loaded into the Zynq RAM on the CTP7?")
        printYellow("\t\t2. OH1 and OH2 screws are properly screwed into their respective standoffs")
        printYellow("\t\t3. OH1 and OH2 standoffs on the GEB are not broken")
        printYellow("\t\t4. Voltage on OH1 standoff is within range [X,Y] Volts")
        printYellow("\t\t5. Voltage on OH2 standoff is within range [X,Y] Volts")
        printRed("Connectivity Testing Failed")
        return
    else:
        printGreen("FPGA Communication Established")
        pass
        
    # Check VFAT Communication
    # =================================================================

    # Scan DACs
    # =================================================================
    from gempython.vfatqc.dacScanV3 import scanAllLinks
    
    from gempython.vfatqc.treeStructure import gemDacCalTreeStructure
    calTree = gemDacCalTreeStructure(
                    name="dacScanTree",
                    nameX="dummy", # temporary name, will be over-ridden
                    nameY=("ADC1" if args.extRefADC else "ADC0"),
                    dacSelect=-1, #temporary value, will be over-ridden 
                    description="GEM DAC Calibration of VFAT3 DAC"
            )
    
    args.stepSize = 1
    for dacSelect in maxVfat3DACSize.keys():
        args.dacSelect = dacSelect
        scanAllLinks(args, calTree, vfatBoard)
        pass

    # Analyze DACs
    # =================================================================

    # Take Scurve
    # =================================================================

    # Analyze Scurve
    # =================================================================

    return


if __name__ == '__main__':
    """
    Placeholder comment
    """

    # create the parser
    import argparse
    parser = ArgumentParser(description="Tool for connectivity testing")

    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("-d","--debug", action="store_true", dest="debug",help = "Print additional debugging information")
    parser.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-m","--maxIter",type=int,help="Maximum number of iterations steps 1-4 will be attempted before failing (and exiting)",default=5)
    parser.add_argument("-o","--ohMask",type=parseInt,help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered",default=0x1)
    parser.add_argument("--shelf",type=int,help="uTCA shelf number",default=2)
    parser.add_argument("-s","--slot",type=int,help="AMC slot in uTCA shelf",default=5)
    args = parser.parse_args()

    # Check inputs
    import os
    if ( (args.slot < 1) or (args.slot > 12) ):
        printRed("Provided AMC slot number {0} is invalid, choose from range [1,12]".format(args.slot))
        exit(os.EX_USAGE)
        pass

    if ( (args.ohMask < 0x0) or (args.ohMask > 0xfff) ):
        printRed("Provided ohMask {0} is invalid, choose from range [0x0,0xfff]".format(hex(args.ohMask)))
        exit(os.EX_USAGE)
        pass

    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.INFO)

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    testConnectivity(args)
