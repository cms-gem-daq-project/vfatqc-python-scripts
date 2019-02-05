#!/bin/env python

from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
from gempython.tools.optohybrid_user_functions_xhal import OHRPCException
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.gemlogger import printGreen, printRed, printYellow

def testConnectivity(args):
    # Get the scandate
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Check if cardName is in args
    if hasattr(args, 'cardName') is False:
        args.cardName = "gem-shelf%02d-amc%02d"%(args.shelf,args.slot)

    # Initialize Hardware
    amc = getAMCObject(args.slot,args.shelf)
    nOHs = readRegister(amc,"GEM_AMC.GEM_SYSTEM.CONFIG.NUM_OF_OH")
    
    vfatBoard = HwVFAT(args.cardName,0) # assign a dummy link for now

    # Check GBT Communication
    # =================================================================
    printYellow("="*20)
    printYellow("Checking GBT Communication")
    printYellow("="*20)

    print("Checking GBT Communication (Before Programming GBTs)")
    if not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask):
        printRed("GBT Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Fibers from GE1/1 patch-panel to OH have correct jacket color ordering")
        printYellow("\t\t2. Fibers from GE1/1 patch-panel to OH are fully inserted")
        printYellow("\t\t3. OH3 screw is properly screwed into standoff")
        printYellow("\t\t4. OH3 standoff on the GEB is not broken")
        printYellow("\t\t5. Voltage on OH3 standoff is within range [1.47,1.59] Volts")
        printRed("Connectivity Testing Failed")
        return

    # Program GBTs
    # placeholder FIXME
    
    print("Checking GBT Communication (After Programming GBTs)")
    if not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask):
        printRed("GBT Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Fibers from GE1/1 patch-panel to OH have correct jacket color ordering")
        printYellow("\t\t2. Fibers from GE1/1 patch-panel to OH are fully inserted")
        printYellow("\t\t3. OH3 screw is properly screwed into standoff")
        printYellow("\t\t4. OH3 standoff on the GEB is not broken")
        printYellow("\t\t5. Voltage on OH3 standoff is within range [1.47,1.59] Volts")
        printRed("Connectivity Testing Failed")
        return
    else: 
        printGreen("GBT Communication Established")
        pass

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
        printYellow("\t\t3. Voltage on OH3 standoff is within range [1.47,1.59] Volts")
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
        printYellow("\t\t4. Voltage on OH1 standoff is within range [0.97,1.06] Volts")
        printYellow("\t\t5. Voltage on OH2 standoff is within range [2.45,2.66] Volts")
        printYellow("\t\t6. Current limit on Power Supply is 4 Amps")
        printRed("Connectivity Testing Failed")
        return
    else:
        printGreen("FPGA Communication Established")
        pass
        
    # Check VFAT Communication
    # =================================================================
    print("Checking GBT Communication (After Programming FPGA)")
    if not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask):
        printRed("GBT Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Current limit on Power Supply is 4 Amps")
        printRed("Connectivity Testing Failed")
        return
    else: 
        printGreen("GBT Communication Established")
        pass

    # Perform N GBT Phase Scans
    # Placeholder FIXME

    # Write Good GBT Phase Values
    # Placeholder FIXME

    print("Checking VFAT Synchronization")
    if not vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=True, printSummary=True,  ohMask=args.ohMask):
        printRed("VFATs are not properly synchronized")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
        printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
        printYellow("\t\t3. The Phase Settings written to each VFAT where in the middle of a 'good' window")
        printRed("Conncetivity Testing Failed")
        return
    else:
        printGreen("VFATs are properly synchronized")
        pass

    print("Checking VFAT Communication")
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_chipIDs = ndict()
    for ohN in range(nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
            
        try:
            dict_chipIDs[ohN] = vfatBoard.getAllChipIDs()
        except OHRPCException as e:
            printRed("VFAT communication was not established successfully for OH{0}".format(ohN))
            printYellow("\tTry checking:")
            printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
            printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
            printYellow("\t\t3. The Phase Settings written to each VFAT where in the middle of a 'good' window")
            printRed("Conncetivity Testing Failed")
            return
        pass

    # Scan DACs
    # =================================================================
    from gempython.vfatqc.utils.scanUtils import dacScanAllLinks 
    
    from gempython.vfatqc.utils.treeStructure import gemDacCalTreeStructure
    calTree = gemDacCalTreeStructure(
                    name="dacScanTree",
                    nameX="dummy", # temporary name, will be over-ridden
                    nameY=("ADC1" if args.extRefADC else "ADC0"),
                    dacSelect=-1, #temporary value, will be over-ridden 
                    description="GEM DAC Calibration of VFAT3 DAC"
            )
   
    vfatBoard.setRunModeAll()

    args.stepSize = 1
    for dacSelect in maxVfat3DACSize.keys():
        args.dacSelect = dacSelect
        dacScanAllLinks(args, calTree, vfatBoard)
        pass

    # Analyze DACs
    # =================================================================
    args.assignXErrors = False
    args.calFileList = None
    args.outfilename = "" # FIXME
    args.printSum = False

    # Placeholder, load parameters for ADC calibration from DB
    # Right now need to rely on someone making the file by hand and placing it in the correct location

    #chamber_config needs to be defined FIXME
    dacAnalysis(args, calTree, chamber_config, scandate='noscandate')

    # Load DAC Values to Front-End
    # =================================================================
    # Going to need to configure...probably need top refactor confChamber FIXME
    from gempython.vfatqc.confChamber import configure


    # Load DAC Values to DB
    # =================================================================
    # Place holder

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
