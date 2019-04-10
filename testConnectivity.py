#!/bin/env python

from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.amc_user_functions_xhal import NoUnmaskedOHException
from gempython.tools.optohybrid_user_functions_xhal import OHRPCException
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.gemlogger import colors, getGEMLogger, printGreen, printRed, printYellow
    
import os

def anaScurveParallel(inputs):
    return scurveAna(*inputs)

def getListOfBadTrigLinks(amcBoard,checkCSCTrigLink=False,debug=False,ohMask=0xfff,printSummary=True):
    """
    Returns a list of OH's with bad trigger links.  A link is considered bad if the sum
    of the link status counters (e.g. GEM_AMC.TRIGGER.OHY.LINK*) do not sum to 0x0


    """
    
    trigLinkStatus = amcBoard.getTriggerLinkStatus(
                        printSummary=printSummary, 
                        checkCSCTrigLink=checkCSCTrigLink, 
                        ohMask=ohMask)

    listOfOHsWithBadTriggerLink = []
    for ohN in range(amcBoard.nOHs):
        # Skip masked OH's
        if( not ((ohMask >> ohN) & 0x1)):
            continue

        # Check Trigger Link Status
        if checkCSCTrigLink:
            if (trigLinkStatus[ohN] == 0 and trigLinkStatus[ohN+1] == 0): # All Good
                if debug:
                    print("Trigger Link for OH{0} is Good".format(ohN))
            elif (trigLinkStatus[ohN] > 0 and trigLinkStatus[ohN+1] == 0): # GEM Trig Link is Bad
                listOfOHsWithBadTriggerLink.append(ohN)
            elif (trigLinkStatus[ohN] == 0 and trigLinkStatus[ohN+1] > 0): # CSC Trig Link is Bad
                listOfOHsWithBadTriggerLink.append(ohN+1)
            else:                                              # Both trigger links are bad
                listOfOHsWithBadTriggerLink.append(ohN)
                listOfOHsWithBadTriggerLink.append(ohN+1)
                pass
            pass
        else:
            if not (trigLinkStatus[ohN] < 1):
                listOfOHsWithBadTriggerLink.append(ohN)
                pass
            pass
        pass

    return listOfOHsWithBadTriggerLink

def gbtCommIsGood(amcBoard, doReset=True, printSummary=True, ohMask=0xfff):
    """
    Determines if GBT communication for all unmasked optohybrids in ohMask is good

        amcBoard     - Instance of HwAMC
        doReset      - If true (false) will (not) perform an GBT link reset
        printSummary - If true (false) will (not) print summary information
        ohMask       - ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered
    """

    if (not amcBoard.getGBTLinkStatus(doReset, printSummary, ohMask)):
        printRed("GBT Communication was not established successfully")
        printYellow("\tTry checking:")
        printYellow("\t\t1. Fibers from GE1/1 patch-panel to OH have correct jacket color ordering")
        printYellow("\t\t2. Fibers from GE1/1 patch-panel to OH are fully inserted")
        printYellow("\t\t3. OH3 screw is properly screwed into standoff")
        printYellow("\t\t4. OH3 standoff on the GEB is not broken")
        printYellow("\t\t5. Voltage on OH3 standoff is within range [1.47,1.59] Volts")
        return False
    else: 
        return True

def scaCommIsGood(amc, maxIter=5, ohMask=0xfff, nOHs=12):
    """
    Determines if SCA communication for all unmasked optohybrids in ohMask is good.
    Will make maxIter number of iterations to establish good communication.

        amc     - instances of uhal device, e.g. returned by getAMCObject from 
                  gempython.tools.amc_user_functions_uhal
        maxIter - maximum number of iterations to be tried before failure is returned
        ohMask  - ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered
    """

    scaCommPassed = False
    from reg_utils.reg_interface.common.sca_utils import sca_reset 
    from reg_utils.reg_interface.common.jtag import initJtagRegAddrs
    initJtagRegAddrs()
    for trial in range(0,maxIter):
        sca_reset(ohMask)
        scaInfo = printSystemSCAInfo(amc)
        
        notRdyCntOkay = True
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((ohMask >> ohN) & 0x1)):
                continue
            
            # Check READY Bit
            if( not ((scaInfo["READY"]  >> ohN) & 0x1)):
                notRdyCntOkay = False
                break

            # Check critical error bit
            if( (scaInfo["CRITICAL_ERROR"] >> ohN) & 0x1):
                notRdyCntOkay = False
                break

            # Check not ready counter
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
    else: 
        printGreen("SCA Communication Established")
        pass

    return scaCommPassed

def scurveAna(scurveDataFile, tuple_calInfo, tuple_deadChan, isVFAT3=True):
    """
    Runs scurve analysis and returns the number of dead channels by VFAT found

    scurveDataFile  - TFile containing the scurveTree
    tuple_calInfo   - Tuple of numpy arrays which provides the CFG_CAL_DAC calibration 
                      where index 0 (1) of the tuple corresponds to the slope (intercept) 
                      array; arrays expected to indexed by VFAT position.
    tuple_deadChan  - Tuple containing scurve sigma range to consider a channel dead/disconnected
    isVFAT3         - True (False) if data comes from VFAT3 (VFAT2)
    """
    
    if len(tuple_deadChan) != 2:
        raise Exception("Length of Provided tuple {0} not equal to 2",os.EX_USAGE)

    # Analyze the scurve
    from gempython.gemplotting.fitting.fitScanData import fitScanData
    scanFitResults = fitScanData(treeFileName=scurveDataFile, isVFAT3=True, calTuple=tuple_calInfo)
    
    deadChanCutLow = min(tuple_deadChan)
    deadChanCutHigh= max(tuple_deadChan)

    nDeadChan = {}

    for vfat in range(0,24):
        for chan in range(0, 128):
            if (deadChanCutLow < scanFitResults[1][vfat][chan] and scanFitResults[1][vfat][chan] < deadChanCutHigh):
                if vfat in nDeadChan.keys():
                    nDeadChan[vfat]+=1
                else:
                    nDeadChan[vfat]=1
                pass
            pass
        pass

    return nDeadChan

def testConnectivity(args):
    # Get the scandate
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Check if all required fields are in args; if they are not assign a default value
    from gempython.vfatqc.utils.qcutilities import getCardName
    if hasattr(args, 'acceptBadTrigLink') is False: # Accept Bad Trigger Link Status?
        args.acceptBadTrigLink = False
    if hasattr(args, 'assignXErrors') is False: # For DAC Scan Analysis
        args.assignXErrors = False
    if hasattr(args, 'calFileList') is False: # For DAC Scan Analysis
       args.calFileList = None
    if hasattr(args, 'cardName') is False:
        args.cardName = getCardName(args.shelf,args.slot)
    if hasattr(args, 'chamberName') is False: # User provided chamberName
        args.chamberName = None
    if hasattr(args, 'chConfig') is False: # Text file containing channel configuration
        args.chConfig = None
    if hasattr(args, 'checkCSCTrigLink') is False: # Using getTriggerLinkStatus with checkCSCTrigLink set to true
        args.checkCSCTrigLink = False
    if hasattr(args, 'compare') is False: # Just Compare frontend settings?
        args.compare = False
    if hasattr(args, 'filename') is False: # TFile containing channel configuration
        args.filename = None
    if hasattr(args, 'nPhaseScans') is False: # Number of GBT Phase Scans to Perform
        args.nPhaseScans = 100
    if hasattr(args, 'outfilename') is False: # Name of DAC Scan Analysis File(s)
        args.outfilename = "DACFitData.root" # dacAnalysis(...) will take care of formating in the subfolder
    if hasattr(args, 'printSum') is False: # For DAC Scan Analysis, do not print summary table
        args.printSum = False
    if hasattr(args, 'run') is False: # Set chips in run mode on configure?
        args.run = False
    if hasattr(args, 'stepSize') is False:
        args.stepSize = 1
    if hasattr(args, 'vt1') is False: # CFG_THR_ARM_DAC (VThreshold1) setting to write for V3 (V2) electronics
        args.vt1 = 100
    if hasattr(args, 'vt1bump') is False: # Value to add to comparator setting
        args.vt1bump = 0
    if hasattr(args, 'vt2') is False: # VThreshold2 value to write if V2 electronics
        args.vt2 = 0
    if hasattr(args, 'vfatConfig') is False: # Text file containing comparator settings
        args.vfatConfig = False
    if hasattr(args, 'voltageStepPulse') is False: # Default to voltageStepPulse in Scurves
        args.voltageStepPulse = True
    if hasattr(args, 'writePhases2File') is False: # Write found GBT Phase seetings to file
        args.writePhases2File = False
    if hasattr(args, 'zeroChan') is False: # Zero all bits in all channel registers
        args.zeroChan = False

    # Check Env Variables & Get Paths
    # =================================================================
    from gempython.utils.wrappers import envCheck, runCommand
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    envCheck("GBT_SETTINGS")
    
    dataPath = os.getenv('DATA_PATH')
    gbtConfigPath = "{0}/OHv3c/20180314".format(os.getenv("GBT_SETTINGS")) # Ideally this would be a DB read...
    elogPath = os.getenv('ELOG_PATH')

    # Initialize Hardware
    amc = getAMCObject(args.slot,args.shelf)
    nOHs = readRegister(amc,"GEM_AMC.GEM_SYSTEM.CONFIG.NUM_OF_OH")
    
    vfatBoard = HwVFAT(args.cardName,0) # assign a dummy link for now

    # Step 1
    # Check GBT Communication
    # =================================================================
    from xhal.reg_interface_gem.core.gbt_utils_extended import configGBT, gbtPhaseScan, setPhaseAllOHs
    if args.firstStep <= 1:
        printYellow("="*20)
        printYellow("Step 1: Checking GBT Communication")
        printYellow("="*20)

        print("Checking GBT Communication (Before Programming GBTs)")
        if not gbtCommIsGood(vfatBoard.parentOH.parentAMC, doReset=True, printSummary=args.debug, ohMask=args.ohMask):
            printRed("Connectivity Testing Failed")
            return

        # Program GBTs
        gbtConfigs = [
                "{0}/GBTX_OHv3c_GBT_0__2018-03-14_FINAL-REG35-42.txt".format(gbtConfigPath),
                "{0}/GBTX_OHv3c_GBT_1__2018-03-14_FINAL-REG35-42.txt".format(gbtConfigPath),
                "{0}/GBTX_OHv3c_GBT_2__2018-03-14_FINAL-REG35-42.txt".format(gbtConfigPath),
                ]
        print("Programming GBTs")
        configGBT(cardName=args.cardName, listOfconfigFiles=gbtConfigs, ohMask=args.ohMask, nOHs=nOHs)

        print("Checking GBT Communication (After Programming GBTs)")
        if not gbtCommIsGood(vfatBoard.parentOH.parentAMC, doReset=True, printSummary=args.debug, ohMask=args.ohMask):
            printRed("Connectivity Testing Failed")
            return
        else: 
            printGreen("GBT Communication Established")
            pass

    # Step 2
    # Check SCA Communication
    # =================================================================
    if args.firstStep <= 2:
        printYellow("="*20)
        printYellow("Step 2: Checking SCA Communication")
        printYellow("="*20)

        scaCommPassed = scaCommIsGood(amc, args.maxIter, args.ohMask, nOHs)

        if not scaCommPassed:
            printRed("Connectivity Testing Failed")
            return

    # Step 3
    # Program FPGA
    # =================================================================
    if args.firstStep <= 3:
        printYellow("="*20)
        printYellow("Step 3: Programming FPGA & Checking Trigger Links")
        printYellow("="*20)

        try:
            listOfDeadFPGAs = vfatBoard.parentOH.parentAMC.programAllOptohybridFPGAs(args.maxIter,args.ohMask)
        except NoUnmaskedOHException:
            printRed("There are no optohybrids that can be programmed successfully")
            printRed("The SCA Communication has probably died")
            printSystemSCAInfo(amc)
            printRed("Connectivity Testing Failed")
            return

        printYellow("SCA Communication Status After FPGA Programming Attempts Is:")
        printSystemSCAInfo(amc)
        
        if len(listOfDeadFPGAs) > 0:
            printRed("FPGA Communication was not established successfully")
            printRed("Following OH's have unprogrammed FPGAs: {0}".format(listOfDeadFPGAs))
            printYellow("\tTry checking:")
            printYellow("\t\t1. OH1 and OH2 screws are properly screwed into their respective standoffs")
            printYellow("\t\t2. OH1 and OH2 standoffs on the GEB are not broken")
            printYellow("\t\t3. Voltage on OH1 standoff is within range [0.97,1.06] Volts")
            printYellow("\t\t4. Voltage on OH2 standoff is within range [2.45,2.66] Volts")
            printYellow("\t\t5. Current limit on Power Supply is 4 Amps")
            printYellow("\t\t6. Power Cycle the affected optohybrids")
            printRed("Connectivity Testing Failed")
            return
        else:
            printGreen("FPGA Communication Established")
            pass

        print("Checking trigger link status:")
        for trial in range(0,args.maxIter):
            if args.debug:
                print("Trial Number: {0}".format(trial))
            
            # Reset trigger module on OH FPGA
            for ohN in range(nOHs):
                if( not ((args.ohMask >> ohN) & 0x1)):
                    continue
                print("Reset trigger module on OH{0}".format(ohN))
                vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.OH.OH{0}.FPGA.TRIG.LINKS.RESET".format(ohN),0x1)

            # Reset trigger module on CTP7 (includes counter reset)
            print("Reseting trigger module on CTP7")
            vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.TRIGGER.CTRL.MODULE_RESET",0x1)

            listOfOHsWithBadTriggerLink = getListOfBadTrigLinks(
                                            vfatBoard.parentOH.parentAMC, 
                                            args.checkCSCTrigLink, 
                                            args.debug,
                                            args.ohMask,
                                            printSummary=True)
            isDead = ( len(listOfOHsWithBadTriggerLink) > 0 )

            # Trigger link status acceptable?
            if not isDead:
                fpgaCommPassed = True
                printGreen("Trigger link to OHs in mask: 0x{0:x} is good".format(args.ohMask))
                break
            elif isDead and not args.acceptBadTrigLink:
                # First try a link reset then check status again
                print("Trigger links for OHs {0} are bad, trying a link reset (GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET 0x1)".format(listOfOHsWithBadTriggerLink))
                vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET",0x1)
                vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.TRIGGER.CTRL.CNT_RESET",0x1)
                listOfOHsWithBadTriggerLink = getListOfBadTrigLinks(
                                                vfatBoard.parentOH.parentAMC, 
                                                args.checkCSCTrigLink, 
                                                args.debug,
                                                args.ohMask,
                                                printSummary=False)
                if (len(listOfOHsWithBadTriggerLink) > 0 ):
                    fpgaCommPassed = False
                    printYellow("Trigger link of OHs: {0} failed, reprogramming OH FPGA's and making another attempt".format(listOfOHsWithBadTriggerLink))
                    try:
                        badFPGAsAfterFWReload = vfatBoard.parentOH.parentAMC.programAllOptohybridFPGAs(args.maxIter,args.ohMask)
                    except NoUnmaskedOHException:
                        printYellow("Reprogramming {0} FPGA's failed, hopefully next iteration succeeds".format(badFPGAsAfterFWReload))
                else:
                    fpgaCommPassed = True
                    printGreen("Trigger link to OHs in mask: 0x{0:x} are now good".format(args.ohMask))
                    break
            else:
                fpgaCommPassed = True
                printYellow("Trigger link of OHs: {0} failed, but I was told to accept bad trigger links".format(listOfOHsWithBadTriggerLink))
                break
            pass

        if not fpgaCommPassed:
            printRed("FPGA trigger link is not healthy")
            printRed("Following OH's have bad trigger links: {0}".format(listOfOHsWithBadTriggerLink))
            printYellow("\tTry checking:")
            printYellow("\t\t1. The trigger fibers from the optohybrid are correctly plugged into the detector patch panel")
            printYellow("\t\t2. Power Cycle the affected optohybrids")
            if args.checkCSCTrigLink:
                printYellow("\t\t3. The trigger fiber from the CSC link to the backend electronics is fully inserted to the detector patch panel")
            printRed("Connectivity Testing Failed")
            return
        else:
            printGreen("Trigger Link Successfully Established")
            pass

    # Step 4
    # Check VFAT Communication
    # =================================================================
    from gempython.utils.nesteddict import nesteddict as ndict
    if args.firstStep <= 4:
        printYellow("="*20)
        printYellow("Step 4: Checking VFAT Communication")
        printYellow("="*20)

        print("Checking GBT Communication (After Programming FPGA)")
        if not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=args.debug, ohMask=args.ohMask):
            printRed("GBT Communication is no longer good after programming FPGA")
            printYellow("\tTry checking:")
            printYellow("\t\t1. Current limit on Power Supply is 4 Amps")
            printRed("Connectivity Testing Failed")
            return
        else: 
            printGreen("GBT Communication Is Stil Good")
            pass

        # Perform N GBT Phase Scans
        print("Scanning GBT Phases, this may take a moment please be patient")
        if args.writePhases2File:
            fName = elogPath+'/gbtPhaseSettings.log'
            dict_phaseScanResults = gbtPhaseScan(cardName=args.cardName, ohMask=args.ohMask, nOHs=nOHs,nOfRepetitions=args.nPhaseScans, silent=(not args.debug), outputFile=fName)
        else:
            dict_phaseScanResults = gbtPhaseScan(cardName=args.cardName, ohMask=args.ohMask, nOHs=nOHs,nOfRepetitions=args.nPhaseScans, silent=(not args.debug))

        # Find Good GBT Phase Values
        failed2FindGoodPhase = False
        dict_phases2Save = {}
        listOfBadVFATs = [ ]
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            dict_phases2Save[ohN] = [ 0xdeaddead for x in range(0,24) ]
            for vfat in range(0,24):
                phaseRes_idxm0 = 0 # Holds Phase Results for phase idx
                phaseRes_idxm1 = 0 # Holds Phase Results for phase idx-1
                phaseRes_idxm2 = 0 # Holds Phase Results for phase idx-2
                phaseRes_idxm3 = 0 # Holds Phase Results for phase idx-3
                phaseRes_idxm4 = 0 # Holds Phase Results for phase idx-4
                phase2Write = -1
                # Initial phase2Write will be phase-1 if 3 consecutive phases are good nScan times
                # This will be overwritten to phase-2 if a 4th consecutive phase is found to be good
                # This will again be overwritten to phase-2 if a 5th consecutive phase is found to be good
                # After 5 consecutive phases are good the procedure will exit
                for phase in range(0,16):
                    phaseRes_idxm0 = dict_phaseScanResults[ohN][vfat*16+phase]

                    if (    phaseRes_idxm4 == args.nPhaseScans and
                            phaseRes_idxm3 == args.nPhaseScans and
                            phaseRes_idxm2 == args.nPhaseScans and 
                            phaseRes_idxm1 == args.nPhaseScans and 
                            phaseRes_idxm0 == args.nPhaseScans): # Found a sweet spot
                        phase2Write = phase-2
                        break
                    elif (  phaseRes_idxm3 == args.nPhaseScans and
                            phaseRes_idxm2 == args.nPhaseScans and
                            phaseRes_idxm1 == args.nPhaseScans and
                            phaseRes_idxm0 == args.nPhaseScans): 
                        phaseRes_idxm4 = phaseRes_idxm3
                        phaseRes_idxm3 = phaseRes_idxm2
                        phaseRes_idxm2 = phaseRes_idxm1
                        phaseRes_idxm1 = phaseRes_idxm0
                        phase2Write = phase-2
                    elif (  phaseRes_idxm2 == args.nPhaseScans and
                            phaseRes_idxm1 == args.nPhaseScans and
                            phaseRes_idxm0 == args.nPhaseScans): 
                        phaseRes_idxm3 = phaseRes_idxm2
                        phaseRes_idxm2 = phaseRes_idxm1
                        phaseRes_idxm1 = phaseRes_idxm0
                        phase2Write = phase-1
                    elif (phaseRes_idxm1 == args.nPhaseScans and phaseRes_idxm0 == args.nPhaseScans): # Last phase and this phase are good
                        phaseRes_idxm2 = phaseRes_idxm1
                        phaseRes_idxm1 = phaseRes_idxm0
                    elif (phaseRes_idxm0 == args.nPhaseScans): # Only this phase is good
                        phaseRes_idxm1 = phaseRes_idxm0
                    else: # Reset
                        phaseRes_idxm0 = 0
                        phaseRes_idxm1 = 0
                        phaseRes_idxm2 = 0
                        phaseRes_idxm3 = 0
                        phaseRes_idxm4 = 0
                        pass
                    pass # End loop over phases
                if phase2Write > -1:
                    printGreen("Phase {0} will be used for (OH{1},VFAT{2})".format(phase2Write,ohN,vfat))
                    dict_phases2Save[ohN][vfat] = phase2Write
                if dict_phases2Save[ohN][vfat] == 0xdeaddead:
                    listOfBadVFATs.append((ohN,vfat))
                    printRed("I did not find a good phase for (OH{0},VFAT{1})".format(ohN,vfat))
                    failed2FindGoodPhase = True
                    pass
                pass # End loop over VFATs
            pass # End loop over OHs

        # Write Found GBT Phase Values
        printGreen("Writing Found Phases to frontend")
        setPhaseAllOHs(args.cardName, dict_phases2Save, args.ohMask, nOHs, args.debug)
        vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET",0x1)

        if (failed2FindGoodPhase and not args.ignoreSyncErrs):
            printRed("GBT Phase Scans Failed to Find Proper Phases")
            printRed("List of Bad (OH,VFAT) pairs: {0}".format(listOfBadVFATs))
            printYellow("\tTry checking:")
            printYellow("\t\t1. OH is firmly inserted into the Samtec Conncetor (press with fingers along connector vias)")
            printYellow("\t\t2. VFATs mentioned above are inserted into the 100-pin connector on the GEB")
            printYellow("\t\t3. VDD on VFATs mentioned above is at least 1.20V")
            printRed("Connectivity Testing Failed")
            return
        if (not failed2FindGoodPhase and args.ignoreSyncErrs):
            printRed("Failed to find proper phases for some (OH,VFAT) pairs.")
            printYellow("But I have been told to ignore sync errors")
        else:
            printGreen("GBT Phases Successfully Writtent to Frontend")
            pass
        pass

    # Step 5
    # Check VFAT Synchronization
    # =================================================================
    from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
    if args.firstStep <= 5:
        printYellow("="*20)
        printYellow("Step 5: Checking VFAT Synchronization")
        printYellow("="*20)

        alllVFATsSyncd = vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask)
        if (not alllVFATsSyncd and not args.ignoreSyncErrs):
            printRed("VFATs are not properly synchronized")
            printYellow("\tTry checking:")
            printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
            printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
            printYellow("\t\t3. The Phase Settings written to each VFAT where in the middle of a 'good' window")
            printRed("Conncetivity Testing Failed")
            return
        if (not alllVFATsSyncd and args.ignoreSyncErrs):
            printRed("VFATs are not properly synchronized")
            printYellow("But I have been told to ignore sync errors")
        else:
            printGreen("VFATs are properly synchronized")
            pass

        dict_vfatMask = vfatBoard.parentOH.parentAMC.getMultiLinkVFATMask(args.ohMask)

        print("Checking VFAT Communication")
        dict_chipIDs = ndict()
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            vfatBoard.parentOH.link = ohN
            try:
                dict_chipIDs[ohN] = vfatBoard.getAllChipIDs(dict_vfatMask[ohN])
            except Exception as e:
                printRed("An exception has occured: {0}".format(e))
                printRed("VFAT communication was not established successfully for OH{0}".format(ohN))
                printYellow("\tTry checking:")
                printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
                printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                printYellow("\t\t3. The Phase Settings written to each VFAT where in the middle of a 'good' window")
                printRed("Conncetivity Testing Failed")
                return
            pass
        pass
        printGreen("VFAT Communication Successfully Established")

    if args.writePhases2File and args.firstStep <= 4:
        fName = elogPath+'/phases.log'
        fPhases = open(fName,"w")
        fPhases.write("link/i:vfatN/i:GBTPhase/i:\n")
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            for vfatN in range(24):
                fPhases.write("{0}\t{1}\t{2}\n".format(ohN,vfatN,dict_phases2Save[ohN][vfatN]))

    # Get the calInfo for all detectors
    # =================================================================
    if (not args.skipDACScan or not args.skipScurve):
        dict_vfat3CalInfo = ndict() # key -> OH number; value -> pandas dataframe
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            vfatBoard.parentOH.link = ohN

            # Get the calibration info for this detector
            dict_vfat3CalInfo[ohN] = getVFAT3CalInfo(dict_chipIDs[ohN],debug=args.debug)
            if args.debug:
                print("dict_vfat3CalInfo[{0}]:\n{1}".format(ohN,dict_vfat3CalInfo[ohN]))

    # Scan DACs
    # =================================================================
    if not args.skipDACScan:
        printYellow("="*20)
        printYellow("Scaning VFAT3 DAC's")
        printYellow("="*20)

        from gempython.vfatqc.utils.treeStructure import gemDacCalTreeStructure
        calTree = gemDacCalTreeStructure(
                        name="dacScanTree",
                        nameX="dummy", # temporary name, will be over-ridden
                        nameY=("ADC1" if args.extRefADC else "ADC0"),
                        dacSelect=-1, #temporary value, will be over-ridden 
                        description="GEM DAC Calibration of VFAT3 DAC"
                )
 
        # Place All Chips Into Run Mode and write correct Iref
        from math import isnan
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            vfatBoard.parentOH.link = ohN

            # First apply IREF settings that are loaded in the CTP7 VFAT3 config files
            # After this do a DB query and overwrite the IREF value
            # This resolves the issue of the chipID having bit flips and generating a fake value causing the DB lookup to fail
            # But it requires the $USER to have set default values on the card if this were to happen
            # Strictly an issue for VFATs that do not use reed-muller encoded chipID's
            print("Setting CFG_IREF for all VFATs on OH{0}".format(ohN))
            vfatBoard.biasAllVFATs(dict_vfatMask[ohN])
            for idx,vfat3CalInfo in dict_vfat3CalInfo[ohN].iterrows():
                if((dict_vfatMask[ohN] >> vfat3CalInfo['vfatN']) & 0x1):
                    continue

                if( not isnan(vfat3CalInfo['iref']) ):
                    try:
                        vfatBoard.writeVFAT(
                                vfat3CalInfo['vfatN'],
                                "CFG_IREF",
                                int(vfat3CalInfo['iref'])) # because apparently the DB stores this as a float >_<
                    except Exception as e:
                        printRed("An exception has occured: {0}".format(e))
                        printRed("VFAT communication was not established successfully for OH{0} VFAT{1}".format(ohN,vfat3CalInfo['vfatN']))
                        vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=False, printSummary=True, ohMask=args.ohMask)
                        printYellow("\tTry checking:")
                        printYellow("\t\t1. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                        printYellow("\t\t2. replacing the red VFATs shown above and then running again")
                        printRed("Conncetivity Testing Failed")
                        return
                    pass
                else:
                    printYellow("CFG_IREF for OH{0} VFAT{1} is {2}".format(ohN,vfat3CalInfo['vfatN'],vfat3CalInfo['iref']))
                pass
            pass

        # DAC Scan
        from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
        from gempython.vfatqc.utils.scanUtils import dacScanAllLinks 
        for dacSelect in maxVfat3DACSize.keys():
            # Skip unnecessary DAC's
            if(dacSelect == 1 or dacSelect == 14 or dacSelect == 15 or dacSelect > 34):
                continue

            args.dacSelect = dacSelect
            try:
                dacScanAllLinks(args, calTree, vfatBoard)
            except Exception as e:
                printRed("An exception has occured: {0}".format(e))
                printRed("DAC Scan for DAC {0} Failed".format(maxVfat3DACSize[dacSelect]))
                vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=False, printSummary=True, ohMask=args.ohMask)
                printYellow("\tTry checking:")
                printYellow("\t\t1. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                printYellow("\t\t2. replacing the red VFATs shown above and then running again")
                printRed("Conncetivity Testing Failed")
                return
            pass
        pass

    # Analyze DACs
    # =================================================================
    # Use stored chamber_config or overwrite chamber_config[ohKey] with user provided name?
    if ( (args.chamberName is not None) and (bin(args.ohMask).count("1") == 1) ):
        chamber_config = {}
        for ohN in range(nOHs):
            if( (args.ohMask >> ohN) & 0x1):
                chamber_config[(args.shelf,args.slot,ohN)] = args.chamberName.replace("/","")
                break
            pass
    else:
        from gempython.gemplotting.mapping.chamberInfo import chamber_config

    if not args.skipDACScan:
        printYellow("="*20)
        printYellow("Analyzing VFAT3 DAC Scan Data")
        printYellow("="*20)

        # Load parameters for ADC calibration
        # Right now need to rely on someone making the file by hand and placing it in the correct location
        # Once Reed-Muller ChipID issue is resolved use the DB query
        if args.extRefADC:
            adcName = "ADC1"
        else:
            adcName = "ADC0"
            pass

        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            ohKey = (args.shelf,args.slot,ohN)

            # If the cal file exists do nothing; otherwise write it from the DB query
            calFileADCName = "{0}/{1}/calFile_{2}_{1}.txt".format(dataPath,chamber_config[ohKey],adcName)
            if not os.path.isfile(calFileADCName):
                if not os.path.exists("{0}/{1}".format(dataPath,chamber_config[ohKey])):
                    runCommand(["mkdir", "-p", "{0}/{1}".format(dataPath,chamber_config[ohKey])])
                    runCommand(["chmod", "g+rw", "{0}/{1}".format(dataPath,chamber_config[ohKey])])
                calFileADC = open(calFileADCName,"w")
                calFileADC.write("vfatN/I:slope/F:intercept/F\n")
                for idx,vfat3CalInfo in dict_vfat3CalInfo[ohN].iterrows():
                    calFileADC.write("{0}\t{1}\t{2}\n".format(
                        vfat3CalInfo['vfatN'],
                        vfat3CalInfo['{0}m'.format(adcName.lower())],
                        vfat3CalInfo['{0}b'.format(adcName.lower())])
                        )
                    pass
                calFileADC.close()
                pass

        # Analyze DAC Scan
        from gempython.gemplotting.utils.anautilities import dacAnalysis
        try:
            dacAnalysis(args, calTree.gemTree, chamber_config, scandate=startTime)
        except Exception as e:
            printRed("An exception has occured: {0}".format(e))
            printRed("DAC Scan Analysis Failed")
            printRed("Conncetivity Testing Failed")
            return
        pass
    
        # Load DAC Values to Front-End
        from gempython.gemplotting.utils.anaInfo import nominalDacValues
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            ohKey = (args.shelf,args.slot,ohN)

            # Write to VFAT3 Config Files
            gemuserHome = "/mnt/persistent/gemuser/"
            for dacName in nominalDacValues.keys():
                if dacName == "CFG_CAL_DAC":
                    continue
                elif dacName == "CFG_THR_ARM_DAC":
                    continue
                elif dacName == "CFG_THR_ZCC_DAC":
                    continue
                elif dacName == "CFG_VREF_ADC":
                    continue
                else:
                    # Copy Files
                    copyFilesCmd = [
                            'scp',
                            '{0}/{1}/dacScans/current/NominalValues-{2}.txt'.format(dataPath,chamber_config[ohKey],dacName),
                            'gemuser@{0}:{1}'.format(args.cardName,gemuserHome)
                            ]
                    runCommand(copyFilesCmd)

                    # Update stored vfat config
                    replaceStr = "/mnt/persistent/gemdaq/scripts/replace_parameter.sh -f {0}/NominalValues-{1}.txt {2} {3}".format(
                            gemuserHome,
                            dacName,
                            dacName.replace("CFG_",""),
                            ohN)
                    transferCmd = [
                            'ssh',
                            'gemuser@{0}'.format(args.cardName),
                            'sh -c "{0}"'.format(replaceStr)
                            ]
                    runCommand(transferCmd)
                    pass
                pass
            pass
        pass
    pass

    # Take Scurve
    # =================================================================
    if not args.skipScurve:
        printYellow("="*20)
        printYellow("Taking a VFAT3 Scurve Scan")
        printYellow("="*20)

        # Configure
        from gempython.vfatqc.utils.confUtils import configure
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            vfatBoard.parentOH.link = ohN
            args.vfatmask = dict_vfatMask[ohN]
            try:
                args.run = False # will be placed into run mode by the call of launchSCurve below
                configure(args, vfatBoard)

                # Ensure Gain is Medium
                vfatBoard.parentOH.broadcastWrite("CFG_RES_PRE",0x2,dict_vfatMask[ohN])
                vfatBoard.parentOH.broadcastWrite("CFG_CAP_PRE",0x1,dict_vfatMask[ohN])
                # Ensure Comp Mode is CFD
                vfatBoard.parentOH.broadcastWrite("CFG_PT",0xf,dict_vfatMask[ohN])
                vfatBoard.parentOH.broadcastWrite("CFG_FP_FE",0x7,dict_vfatMask[ohN])
                vfatBoard.parentOH.broadcastWrite("CFG_SEL_COMP_MODE",0x0,dict_vfatMask[ohN])
                vfatBoard.parentOH.broadcastWrite("CFG_FORCE_EN_ZCC",0x0,dict_vfatMask[ohN])
            except Exception as e:
                printRed("An exception has occured: {0}".format(e))
                printRed("Failed to configure OH{0}".format(ohN))
                vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=False, printSummary=True, ohMask=args.ohMask)
                printYellow("\tTry checking:")
                printYellow("\t\t1. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                printYellow("\t\t2. replacing the red VFATs shown above and then running again")
                printRed("Conncetivity Testing Failed")
                return
            pass
        printGreen("All Chambers Configured")

        scurveFiles = {}
        from gempython.vfatqc.utils.scanUtils import launchSCurve, makeScanDir
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            
            ohKey = (args.shelf,args.slot,ohN)
        
            dirPath = makeScanDir(args.slot, ohN, "scurve", startTime, args.shelf, chamber_config)
            dirPath += "/{}".format(startTime)
            logFile = "%s/scanLog.log"%(dirPath)
            scurveFiles[ohN] = "{0}/{1}/scurve/{2}/SCurveData.root".format(dataPath,chamber_config[ohKey],startTime)

            vfatBoard.parentOH.link = ohN
            try:
                launchSCurve(
                        cardName = args.cardName,
                        debug = args.debug,
                        filename = scurveFiles[ohN],
                        link = ohN,
                        logFile = logFile,
                        vfatmask = dict_vfatMask[ohN],
                        voltageStepPulse = args.voltageStepPulse)
            except Exception as e:
                printRed("An exception has occured: {0}".format(e))
                printRed("SCurve for OH{0} Failed".format(ohN))
                vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=False, printSummary=True, ohMask=args.ohMask)
                printYellow("\tTry checking:")
                printYellow("\t\t1. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                printYellow("\t\t2. replacing the red VFATs shown above and then running again")
                printRed("Conncetivity Testing Failed")
                return
            pass
        printGreen("All SCurves Completed")
        pass

    # Analyze Scurve
    # =================================================================
    from gempython.gemplotting.utils.anautilities import parseCalFile
    if not args.skipScurve:
        printYellow("="*20)
        printYellow("Analyzing VFAT3 Scurve Scan Data")
        printYellow("="*20)

        # Load CFG_CAL_DAC calibration from DB
        # Right now need to rely on someone making the file by hand and placing it in the correct location
        # Once Reed-Muller ChipID issue is resolved use the DB query
        calDacInfo = ndict()
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
        
            ohKey = (args.shelf,args.slot,ohN)

            # If the cal file exists parse it; otherwise write it from the DB query
            calFileCALDacName = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[ohKey])
            if os.path.isfile(calFileCALDacName):
                calDacInfo[ohN] = parseCalFile(calFileCALDacName)
            else:
                if not os.path.exists("{0}/{1}".format(dataPath,chamber_config[ohKey])):
                    runCommand(["mkdir", "-p", "{0}/{1}".format(dataPath,chamber_config[ohKey])])
                    runCommand(["chmod", "g+rw", "{0}/{1}".format(dataPath,chamber_config[ohKey])])
                calFileCALDac = open(calFileCALDacName,"w")
                calFileCALDac.write("vfatN/I:slope/F:intercept/F\n")
                for idx,vfat3CalInfo in dict_vfat3CalInfo[ohN].iterrows():
                    calFileCALDac.write("{0}\t{1}\t{2}\n".format(
                        vfat3CalInfo['vfatN'],
                        vfat3CalInfo['cal_dacm'],
                        vfat3CalInfo['cal_dacb'])
                        )
                    pass
                calFileCALDac.close()
                calDacInfo[ohN] = (vfat3CalInfo['cal_dacm'],vfat3CalInfo['cal_dacb'])
                pass
        
        # Dead chan
        deadChan = tuple([float(x) for x in args.deadChanCuts.split(",")])

        # Setup a pool
        from multiprocessing import Pool
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        pool = Pool(bin(args.ohMask).count("1"))
        signal.signal(signal.SIGINT, original_sigint_handler)
        
        if vfatBoard.parentOH.parentAMC.fwVersion > 1:
            isVFAT3 = True
        else:
            isVFAT3 = False

        # Launch the pool processes
        from reg_utils.reg_interface.common.sca_common_utils import getOHlist
        ohList = getOHlist(args.ohMask)

        import itertools
        try:
            res = pool.map_async(anaScurveParallel,
                    itertools.izip(
                        [scurveFiles[x] for x in ohList],
                        [calDacInfo[x]  for x in ohList],
                        [deadChan       for x in ohList],
                        [isVFAT3        for x in ohList]
                        )
                    )
            nDeadChanByOH = res.get(3600) # wait at most 1 hour
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            printRed("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()
            printRed("Conncetivity Testing Failed")
            return 
        except Exception as e:
            print("Caught Exception %s, terminating workers"%(str(e)))
            pool.terminate()
            printRed("Conncetivity Testing Failed")
            return 
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            print("Caught non-Python Exception %s"%(e))
            pool.terminate()
            printRed("Conncetivity Testing Failed")
            return 
        else:
            printGreen("SCurve Analysis Completed Successfully")

        print("| OH | VFAT | N_DEAD |")
        print("| -- | ---- | ------ |")
        tooManyDeadChan = False
        sumDeadChan = 0
        for ohN,ResultsByVfat in enumerate(nDeadChanByOH):
            for vfat,nDeadChan in ResultsByVfat.iteritems():
                print("| {0} | {1} | {2}{3}{4} |".format(ohN,vfat,colors.RED if nDeadChan > 0 else colors.GREEN,nDeadChan,colors.ENDC))
                sumDeadChan+=nDeadChan
                if sumDeadChan > 3:
                    tooManyDeadChan = True
                    pass
                pass
            pass

        if tooManyDeadChan:
            printRed("Too Many Dead Channels")
            printRed("Conncetivity Testing Failed")
            return 
        else:
            printGreen("Number of Dead Channels is Acceptable")
            pass
        pass

    # If we got here we are done
    printGreen("Connectivity Testing Passed for OH's in {0}".format(hex(args.ohMask)))

    return 0

if __name__ == '__main__':
    """
    Placeholder comment
    """

    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="Tool for connectivity testing")

    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("-c","--chamberName",type=str,help="Detector Serial Number, if provided will use this name instead of name provided in chamber_config dictionary",default=None)
    parser.add_argument("--checkCSCTrigLink",action="store_true",help="Check also the trigger link for the CSC trigger associated to OH in mask")
    parser.add_argument("--deadChanCuts",type=str,help="Comma separated pair of integers specifying in fC the scurve width to consider a channel dead",default="0.1,0.5")
    parser.add_argument("-a","--acceptBadTrigLink",action="store_true",help="Ignore failing trigger link status checks")
    parser.add_argument("-d","--debug",action="store_true",dest="debug",help = "Print additional debugging information")
    parser.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-f","--firstStep",type=int,help="Starting Step of connectivity testing, to skip all initial steps enter '5'",default=1)
    parser.add_argument("-i","--ignoreSyncErrs",action="store_true",help="Ignore VFAT Sync Errors When Checking Communication")
    parser.add_argument("-m","--maxIter",type=int,help="Maximum number of iterations steps 2 & 3 will be attempted before failing (and exiting)",default=10)
    parser.add_argument("-n","--nPhaseScans",type=int,help="Number of gbt phase scans to perform when determining vfat phase assignment",default=100)
    parser.add_argument("-o","--ohMask",type=parseInt,help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered",default=0x1)
    parser.add_argument("--shelf",type=int,help="uTCA shelf number",default=2)
    parser.add_argument("--skipDACScan",action="store_true",help="Do not perform any DAC Scans")
    parser.add_argument("--skipScurve",action="store_true",help="Do not perform any SCurves")
    parser.add_argument("-s","--slot",type=int,help="AMC slot in uTCA shelf",default=5)
    parser.add_argument("--writePhases2File",action="store_true",help="Write found GBT Phase seetings to file")
    args = parser.parse_args()

    # Check inputs
    if ( (args.slot < 1) or (args.slot > 12) ):
        printRed("Provided AMC slot number {0} is invalid, choose from range [1,12]".format(args.slot))
        exit(os.EX_USAGE)
        pass

    if ( (args.ohMask < 0x0) or (args.ohMask > 0xfff) ):
        printRed("Provided ohMask {0} is invalid, choose from range [0x0,0xfff]".format(hex(args.ohMask)))
        exit(os.EX_USAGE)
        pass

    if args.firstStep > 5:
        printRed("The starting step number {0} you entered is outside the range of possible values: [1,5]".format(args.firstStep))
        exit(os.EX_USAGE)
        pass

    if ((args.firstStep >= 5) and (args.skipDACScan and args.skipScurve)):
        printRed("Sorry but you're asking me to skip all initial steps and all follow-up steps")
        printRed("This doesn't make sense; please reconsider")
        exit(os.EX_USAGE)
        pass

    # Enforce a minimum number of phase scans
    if args.nPhaseScans < 100:
        printYellow("You've requested the number of phase scans to be {0} which is less than 100.\nThis is probably not reliable, reseting to 100".format(args.nPhaseScans))
        args.nPhaseScans = 100
        pass

    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.INFO)

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    testConnectivity(args)

    print("Goodbye")
