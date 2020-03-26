#!/bin/env python

from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.amc_user_functions_xhal import NoUnmaskedOHException
from gempython.tools.hw_constants import gemVariants, GBT_PHASE_RANGE, vfatsPerGemVariant
from gempython.tools.optohybrid_user_functions_xhal import OHRPCException, OHTypeException
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.gemlogger import colors, getGEMLogger, printGreen, printRed, printYellow

import os

def anaScurveParallel(inputs):
    return scurveAna(*inputs)

def getListOfBadTrigLinks(amcBoard,checkCSCTrigLink=False,debug=False,ohMask=0xfff,printSummary=True):
    """
    Returns a list of OH's with bad trigger links.  A link is considered bad if the sum
    of the link status counters (e.g. GEM_AMC.TRIGGER.OHY.LINK*) do not sum to 0x0

        amcBoard         - Instance of HwAMC class
        checkCSCTrigLink - If true checks the CSC trigger link in addition to the GEM trigger link
        debug            - prints additional debugging info
        ohMask           - 12 bit number, a 1 in the N^th bit means consider the N^th optohybrid
        printSummary     - If true prints a summary table of the results
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

def gbtCommIsGood(amcBoard, doReset=True, printSummary=True, ohMask=0xfff, gemType="ge11"):
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
    from gempython.utils.registers_uhal import writeRegister
    from reg_utils.reg_interface.common.sca_utils import sca_reset
    from reg_utils.reg_interface.common.jtag import initJtagRegAddrs
    initJtagRegAddrs()

    try:
        writeRegister(amc,"GEM_AMC.SLOW_CONTROL.SCA.ADC_MONITORING.MONITORING_OFF",0xffffffff)
    except uhal._core.exception:
        printYellow("An exception has been caught while attempting to disable the ADC monitoring.")
        printYellow("If you use a CTP7 with a firmware version higher than 3.8.3 you can safely ignore this warning.")
        pass

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
    if hasattr(args, 'acceptBadDACBiases') is False: # Accept Bad cases where a VFAT DAC cannot reach correct bias voltage/current
        args.acceptBadDACBiases = False
    if hasattr(args, 'acceptBadDACFits') is False: # Accept Bad cases where a VFAT DAC cannot reach correct bias voltage/current
        args.acceptBadDACFits = False
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
    if hasattr(args, 'detType') is False:
        args.detType = "short" # default to short
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
    if hasattr(args, 'gemType') is False:
        args.gemType = "ge11" # default to ge11
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
    if args.gemType == "ge11":
        gbtConfigPath = "{0}/OHv3c/".format(os.getenv("GBT_SETTINGS")) # Ideally this would be a DB read...
    elif args.gemType == "ge21":
        gbtConfigPath = "{0}/OHGE21/".format(os.getenv("GBT_SETTINGS"))
    else:
        print("me0 gemType not currently implemented, exiting.")
        printRed("Connectvity Testing Failed")
        return

    elogPath = os.getenv('ELOG_PATH')

    # Initialize Hardware
    amc = getAMCObject(args.slot,args.shelf)
    nOHs = readRegister(amc,"GEM_AMC.GEM_SYSTEM.CONFIG.NUM_OF_OH")

    try:
        vfatBoard = HwVFAT(
                args.cardName,
                link=0,                 # assign a dummy link for now
                gemType=args.gemType,
                detType=args.detType)        # assign a dummy detType for now
    except OHTypeException as err:
        printYellow(err.message)
        printRed("Connectivity Testing Failed")
        return

    # Block L1A's before doing anything else
    blockL1A(amc)

    # Step 1
    # Check GBT Communication
    # =================================================================
    from xhal.reg_interface_gem.core.gbt_utils_extended import configGBT, gbtPhaseScan, setPhaseAllOHs
    if args.firstStep <= 1:
        printYellow("="*20)
        printYellow("Step 1: Checking GBT Communication")
        printYellow("="*20)

        print("Checking GBT Communication (Before Programming GBTs)")
        if not gbtCommIsGood(vfatBoard.parentOH.parentAMC, doReset=True, printSummary=args.debug, ohMask=args.ohMask, gemType=args.gemType):
            printRed("Connectivity Testing Failed")
            printYellow("If Vmon = 8.0V then Imon must be 1.71 +/- 0.01A; if not the GBT's are not locking to the fiber link")
            return

        # Program GBTs
        if args.gemType == "ge11":
            gbtConfigs = [
                "{0}/GBTX_OHv3c_GBT_0.txt".format(gbtConfigPath),
                "{0}/GBTX_OHv3c_GBT_1.txt".format(gbtConfigPath),
                "{0}/GBTX_OHv3c_GBT_2.txt".format(gbtConfigPath),
                ]
        elif args.gemType == "ge21":
            gbtConfigs = [
                "{0}/GBTX_GE21_OHv1_GBT_0.txt".format(gbtConfigPath),
                "{0}/GBTX_GE21_OHv1_GBT_1.txt".format(gbtConfigPath),
                ]
        else:
            print("me0 gemType not currently implemented, exiting.")
            exit(os.EX_USAGE)

        print("Programming GBTs")
        configGBT(cardName=args.cardName, listOfconfigFiles=gbtConfigs, ohMask=args.ohMask, nOHs=nOHs)

        print("Checking GBT Communication (After Programming GBTs)")
        if not gbtCommIsGood(vfatBoard.parentOH.parentAMC, doReset=True, printSummary=args.debug, ohMask=args.ohMask, gemType=args.gemType):
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
    if (args.firstStep <= 4) and not args.skipGBTPhaseScan:
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
            fNameGBTPhaseScanResults = elogPath+'/gbtPhaseSettings.log'
            dict_phaseScanResults = gbtPhaseScan(cardName=args.cardName, ohMask=args.ohMask, nOHs=nOHs,nOfRepetitions=args.nPhaseScans, silent=False, outputFile=fNameGBTPhaseScanResults, nVFAT=vfatBoard.parentOH.nVFATs, nVerificationReads=args.nVerificationReads)
        else:
            dict_phaseScanResults = gbtPhaseScan(cardName=args.cardName, ohMask=args.ohMask, nOHs=nOHs,nOfRepetitions=args.nPhaseScans, silent=False, nVFAT=vfatsPerGemVariant[args.gemType], nVerificationReads=args.nVerificationReads)

        # Find Good GBT Phase Values
        failed2FindGoodPhase = False
        dict_phases2Save = {}
        listOfBadVFATs = [ ]
        vfats2Replace = [ ]
        MAX_BAD_PHASES = 5 ## maybe migrate this, maybe not
        PHASE_WINDOW   = 4 ## Good phase search window
        PHASE_SHIFT    = 4 ## Phase shift from bad phase to set
        from gempython.gemplotting.mapping.chamberInfo import GEBtype
        from gempython.vfatqc.utils.phaseUtils import crange,getSequentialBadPhases, getPhaseFromLongestGoodWindow, phaseIsGood
        import numpy as np
        for ohN in range(nOHs):
            # Skip masked OH's
            if ( not ((args.ohMask >> ohN) & 0x1)):
                continue

            # Update the hardware info
            vfatBoard.parentOH.link = ohN
            if args.detType is not None:
                try:
                    vfatBoard.parentOH.setType(args.gemType, args.detType)
                except OHTypeException as err:
                    printYellow(err.message)
                    printRed("Connectivity Testing Failed")
                    return
                pass
            else:
                ohKey = (args.shelf,args.slot,ohN)
                detType = GEBtype[ohKey]
                try:
                    vfatBoard.parentOH.setType(args.gemType, detType)
                except OHTypeException as err:
                    printYellow(err.message)
                    printRed("Connectivity Testing Failed")
                    return
                pass

            dict_phases2Save[ohN] = [ 0xf for x in range(0,vfatsPerGemVariant[args.gemType]) ] #Start by setting all phases as bad (e.g. 15)
            for vfat in range(vfatsPerGemVariant[args.gemType]):
                phase2Write = -1
                phaseCounts = np.array([ dict_phaseScanResults[ohN][vfat*GBT_PHASE_RANGE+ph] for ph in range(0,GBT_PHASE_RANGE) ])
                allBadPhases = np.where(phaseCounts!=args.nPhaseScans)[0]
                badPhaseCounts = np.delete(allBadPhases,np.where(allBadPhases==15)[0]) ## remove 15 from the list of bad phases
                phaseSum = 0
                if len(badPhaseCounts) == 0:
                    # First try to set the phase from the lookup table
                    if phaseIsGood(vfatBoard, vfat, vfatBoard.parentOH.vfatGBTPhases):
                        phase2Write = vfatBoard.parentOH.vfatGBTPhases[vfat]
                    else:
                        # Wonder if this could be done with a lambda...probably not
                        tmpPhase = -1
                        if (vfatBoard.parentOH.vfatGBTPhases[vfat] + PHASE_SHIFT) < 15:
                            tmpPhase = vfatBoard.parentOH.vfatGBTPhases[vfat] + PHASE_SHIFT
                        else:
                            tmpPhase = vfatBoard.parentOH.vfatGBTPhases[vfat] - PHASE_SHIFT
                            pass

                        if phaseIsGood(vfatBoard, vfat, tmpPhase):
                            phase2Write = tmpPhase
                            pass
                        pass

                    if (not (phase2Write > -1)):
                        vfats2Replace.append((ohN,vfat))
                elif len(badPhaseCounts) > MAX_BAD_PHASES:
                    printRed("There were more than {0} bad phases for (OH{1},VFAT{2})".format(MAX_BAD_PHASES,ohN,vfat))
                else:
                    for bPhase in badPhaseCounts:
                        frange  = crange(int(bPhase+1),
                                         int(bPhase+1)+PHASE_WINDOW,
                                         GBT_PHASE_RANGE)
                        brange  = crange(int(bPhase)-PHASE_WINDOW,
                                         int(bPhase),
                                         GBT_PHASE_RANGE)
                        fsum = sum(phaseCounts.take(frange, mode='wrap')) # forward  sum
                        bsum = sum(phaseCounts.take(brange, mode='wrap')) # backward sum
                        tmpPhase = 15
                        if fsum > phaseSum:
                            lphase = int((bPhase+PHASE_SHIFT)%GBT_PHASE_RANGE)
                            if phaseCounts[lphase] == args.nPhaseScans:
                                phaseSum = fsum
                                tmpPhase = lphase
                        if bsum > phaseSum:
                            lphase = int((bPhase-PHASE_SHIFT)%GBT_PHASE_RANGE)
                            if phaseCounts[lphase] == args.nPhaseScans:
                                phaseSum = bsum
                                tmpPhase = lphase

                        if tmpPhase != 15:
                            if phaseCounts[tmpPhase] == args.nPhaseScans:  ## now redundant, can remove
                            # if phaseIsGood(vfatBoard, vfat, tmpPhase):
                                phase2Write = tmpPhase
                # FIXME REMOVE BLOCK, OLD ALGO
                if True:
                    pass
                elif len(badPhaseCounts) == 1:
                    phase2Write = getPhaseFromLongestGoodWindow(badPhaseCounts[0],phaseCounts)
                elif len(badPhaseCounts) == 2:
                    # check if bad phases are sequential, if so use the longest good window
                    # if bad phases are not sequential use the midpoint, ignore wraparound
                    tuple_seqBadPhases = getSequentialBadPhases(badPhaseCounts)

                    badPhasesAreSequential = tuple_seqBadPhases[0]
                    minSeqPhase = tuple_seqBadPhases[1]
                    maxSeqPhase = tuple_seqBadPhases[2]

                    if(badPhasesAreSequential):
                        phase2Write = getPhaseFromLongestGoodWindow(minSeqPhase,phaseCounts)
                    else:
                        phase2Write = int((badPhaseCounts[1] - badPhaseCounts[0])/2+badPhaseCounts[0])
                        pass
                    pass
                elif len(badPhaseCounts) == 3:
                    # check if bad phases are sequential, if so use pick the midpoint, ignore wraparound
                    # if bad phases are not sequential just look for the longest good window
                    tuple_seqBadPhases = getSequentialBadPhases(badPhaseCounts)

                    badPhasesAreSequential = tuple_seqBadPhases[0]
                    minSeqPhase = tuple_seqBadPhases[1]
                    maxSeqPhase = tuple_seqBadPhases[2]
                    idx2Use     = tuple_seqBadPhases[3]

                    if (badPhasesAreSequential): # Look for midpoint
                        if badPhaseCounts[idx2Use[0]] > maxSeqPhase:
                            phase2Write = int((badPhaseCounts[idx2Use[0]] - maxSeqPhase)/2+maxSeqPhase)
                        else:
                            phase2Write = int((minSeqPhase - badPhaseCounts[idx2Use[0]])/2+badPhaseCounts[idx2Use[0]])
                            pass
                        pass
                    else:                       # Look for longest good window
                        badPhaseCounts = np.sort(badPhaseCounts)
                        ranges = []
                        ranges.append(range(0,int(badPhaseCounts[0])+1))
                        ranges.append(range(int(badPhaseCounts[0])+1,int(badPhaseCounts[1])+1))
                        ranges.append(range(int(badPhaseCounts[1])+1,int(badPhaseCounts[2])+1))
                        ranges.append(range(int(badPhaseCounts[2])+1,16))
                        rangeLengths = [ len(x) for x in ranges ]
                        idxOfRanges = rangeLengths.index(max(rangeLengths))
                        ranges[idxOfRanges].sort() # don't think this is necessary?
                        phase2Write = int((ranges[idxOfRanges][-1] - ranges[idxOfRanges][0])/2 + ranges[idxOfRanges][0])
                    pass
                elif len(badPhaseCounts) == 4:
                    # check if there exists two pairs of sequential bad phases, if so pick the midpoint, ignore wraparound
                    # placeholder
                    pass
                else:
                    # more than 3 bad phases, shouldn't happen, how to treat?
                    pass

                if phase2Write > -1:
                    printGreen("Phase {0} will be used for (OH{1},VFAT{2})".format(phase2Write,ohN,vfat))
                    dict_phases2Save[ohN][vfat] = phase2Write
                if dict_phases2Save[ohN][vfat] == 0xf:
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
            printYellow("\t\t4. Replace the (OH,VFAT) pairs {0} with new hybrids if possible".format(vfats2Replace))
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

        if args.skipGBTPhaseScan:
            printYellow("Some VFATs may not be synchronized since I did not perform a GBT Phase Scan")

        alllVFATsSyncd = vfatBoard.parentOH.parentAMC.getVFATLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask)
        if (not alllVFATsSyncd and not args.ignoreSyncErrs):
            printRed("VFATs are not properly synchronized")
            if args.skipGBTPhaseScan:
                printYellow("I warned you this might happen because the GBT Phase scan was not performed.\nYou might want to call this routine again but drop the '--skipGBTPhaseScan' argument")
            else:
                printYellow("\tTry checking:")
                printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
                printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
                printYellow("\t\t3. The Phase Settings written to each VFAT were in the middle of a 'good' window")
            printRed("Conncetivity Testing Failed")
            return
        if (not alllVFATsSyncd and args.ignoreSyncErrs):
            printRed("VFATs are not properly synchronized")
            if args.skipGBTPhaseScan:
                printYellow("I warned you this might happen because the GBT Phase scan was not performed.\nYou might want to call this routine again but drop the '--skipGBTPhaseScan' argument")
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
                printYellow("\t\t3. The Phase Settings written to each VFAT were in the middle of a 'good' window")
                printRed("Conncetivity Testing Failed")
                return
            pass
        pass
        printGreen("VFAT Communication Successfully Established")

    if args.writePhases2File and args.firstStep <= 4 and not args.skipGBTPhaseScan:
        fNameGBTPhaseSetPts = elogPath+'/phases.log'
        fPhases = open(fNameGBTPhaseSetPts,"w")
        fPhases.write("link/i:vfatN/i:GBTPhase/i:\n")
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            for vfatN in range(vfatsPerGemVariant[args.gemType]):
                fPhases.write("{0}\t{1}\t{2}\n".format(ohN,vfatN,dict_phases2Save[ohN][vfatN]))
                pass
            pass
        fPhases.close()

        from gempython.gemplotting.utils.anautilities import getPhaseScanPlots, getSinglePhaseScanPlot
        if( (args.chamberName is not None) and (bin(args.ohMask).count("1") == 1) ):
            # Case specific detector, make one plot
            link = -1
            for ohN in range(nOHs):
                if((args.ohMask >> ohN) & 0x1):
                    link = ohN
                    break
                pass

            getSinglePhaseScanPlot(link,fNameGBTPhaseScanResults,fNameGBTPhaseSetPts,args.chamberName,savePlots=True)
        else:
            # Case possibly multi detectors, make grid plot
            getPhaseScanPlots(fNameGBTPhaseScanResults,fNameGBTPhaseSetPts,savePlots=True)
            pass

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

        printYellow("CAlTree retrieved")
        # Place All Chips Into Run Mode and write correct Iref
        from math import isnan
        for ohN in range(nOHs):
            printRed("Checking whether OH%s is masked" %(ohN))
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
        from gempython.gemplotting.utils.exceptions import VFATDACBiasCannotBeReached
        from gempython.gemplotting.utils.exceptions import VFATDACFitLargeChisquare
        try:
            dacAnalysis(args, calTree.gemTree, chamber_config, scandate=startTime)
        except VFATDACFitLargeChisquare as e:
            printRed("One or more VFATs has a bad (large chisquare) DAC vs ADC fit")
            printRed(e.message)
            if not args.acceptBadDACFits:
                printRed("DAC Scan Analysis Failed")
                printRed("Conncetivity Testing Failed")
                return
            else:
                printYellow("I've been told to ignore cases of VFATs having bad DAC vs ADC fits; results may not be so good")
        except VFATDACBiasCannotBeReached as e:
            printRed("One or more VFATs is unable to reach the correct bias voltage/current setpoint")
            printRed(e.message)
            if not args.acceptBadDACBiases:
                printRed("DAC Scan Analysis Failed")
                printRed("Conncetivity Testing Failed")
                return
            else:
                printYellow("I've been told to ignore cases of VFATs failing to hit the correct bias voltage/current setpoints; results may not be so good")
        except ValueError as e:
            printRed("ValueError has occurred")
            printRed(e.message)
            printRed("DAC Scan Analysis Failed")
            printRed("Conncetivity Testing Failed")
            return
        except RuntimeError as e:
            printRed("Runtime Error has occurred")
            printRed(e.message)
            printRed("DAC Scan Analysis Failed")
            printRed("Conncetivity Testing Failed")
            return
        except Exception as e:
            printRed("An unexpected exception has occured: {0}".format(e))
            printRed(e.message)
            printRed("DAC Scan Analysis Failed")
            printRed("Conncetivity Testing Failed")
            return
        pass

        # Load DAC Values to Front-End
        from gempython.gemplotting.utils.anaInfo import nominalDacValues
        from gempython.vfatqc.utils.confUtils import updateVFAT3ConfFilesOnAMC
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
                    nomValFile='{0}/{1}/dacScans/current/NominalValues-{2}.txt'.format(dataPath,chamber_config[ohKey],dacName)
                    updateVFAT3ConfFilesOnAMC(args.cardName,ohN,nomValFile,dacName)
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
                        voltageStepPulse = args.voltageStepPulse,
                        gemType = args.gemType,
                        detType = args.detType)
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

    # Required Arguments
    parser.add_argument("shelf",type=int,help="uTCA shelf number")
    parser.add_argument("slot",type=int,help="AMC slot in uTCA shelf")
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("ohMask",type=parseInt,help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered")

    parser.add_argument("-c","--chamberName",type=str,help="Detector Serial Number, if provided will use this name instead of name provided in chamber_config dictionary",default=None)
    parser.add_argument("--checkCSCTrigLink",action="store_true",help="Check also the trigger link for the CSC trigger associated to OH in mask")
    parser.add_argument("--deadChanCuts",type=str,help="Comma separated pair of integers specifying in fC the scurve width to consider a channel dead",default="0.1,0.5")
    parser.add_argument("--acceptBadDACBiases",action="store_true",help="Ignore failures where a VFAT DAC cannot reach the correct bias voltage/current")
    parser.add_argument("--acceptBadDACFits",action="store_true",help="Ignore cases where a VFAT DAC vs ADC fit has a large chisquare")
    parser.add_argument("-a","--acceptBadTrigLink",action="store_true",help="Ignore failing trigger link status checks")
    parser.add_argument("-d","--debug",action="store_true",dest="debug",help = "Print additional debugging information")
    parser.add_argument("--detType",type=str,help="Detector type within gemType. If gemType is 'ge11' then this should be from list {0}; if gemType is 'ge21' then this should be from list {1}; and if type is 'me0' then this should be from the list {2}".format(gemVariants['ge11'],gemVariants['ge21'],gemVariants['me0']),default=None)
    parser.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-f","--firstStep",type=int,help="Starting step of connectivity testing, to skip all initial steps enter '5'",default=1)
    parser.add_argument("--gemType",type=str,help="String that defines the GEM variant, available from the list: {0}".format(gemVariants.keys()),default="ge11")
    parser.add_argument("-i","--ignoreSyncErrs",action="store_true",help="Ignore VFAT Sync Errors When Checking Communication")
    parser.add_argument("-m","--maxIter",type=int,help="Maximum number of iterations steps 2 & 3 will be attempted before failing (and exiting)",default=1)
    parser.add_argument("-n","--nPhaseScans",type=int,help="Number of gbt phase scans to perform when determining vfat phase assignment",default=50)
    parser.add_argument("--nVerificationReads",type=int,help="Number of verification reads to be performed during GBT phase scan",default=10)
    parser.add_argument("--skipDACScan",action="store_true",help="Do not perform any DAC Scans")
    parser.add_argument("--skipGBTPhaseScan",action="store_true",help="Do not perform any GBT Phase Scans")
    parser.add_argument("--skipScurve",action="store_true",help="Do not perform any SCurves")
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

    args.gemType = args.gemType.lower()
    if args.gemType not in gemVariants.keys():
        printYellow("gemType '{0}' not in the list of known gemVariants: {1}".format(args.gemType,gemVariants.keys()))
        printYellow("please relaunch using --gemType from the above list")
        printRed("Connectivity Testing Failed")
        exit(os.EX_USAGE)

    if args.detType is not None:
        args.detType = args.detType.lower()
        if args.detType not in gemVariants[args.gemType]:
            printYellow("detType '{0}' not in the list of known detector types for gemType {1}; list of known detector types: {2}".format(args.detType, args.gemType, gemVariants[args.gemType]))
            printYellow("please relaunch using --detType from the above list")
            printRed("Connectivity Testing Failed")
            exit(os.EX_USAGE)

    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.INFO)

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    testConnectivity(args)

    print("Goodbye")
