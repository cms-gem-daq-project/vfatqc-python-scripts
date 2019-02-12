#!/bin/env python

from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.optohybrid_user_functions_xhal import OHRPCException
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.gemlogger import getGEMLogger, printGreen, printRed, printYellow
    
import os

def anaScurveParallel(inputs):
    return scurveAna(*inputs)

def scurveAna(scurveDataFile, tuple_calInfo, tuple_deadChan, isVFAT3=True):
    """
    Runs scurve analysis and returns the number of dead channels found

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
    scanFitResults = fitScanData(treeFileName=filename, isVFAT3=True, calTuple=tuple_calInfo)
    
    deadChanCutLow = min(tuple_deadChan)
    deadChanCutHigh= max(tuple_deadChan)

    nDeadChan = 0

    for vfat in range(0,24):
        for chan in range(0, 128):
            if (deadChanCutLow < scanFitResults[1][vfat][chan] and canFitResults[1][vfat][chan] < deadChanCutHigh):
                nDeadChan+=1
                pass
            pass
        pass

    return nDeadChan

def testConnectivity(args):
    # Get the scandate
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Check if all required fields are in args; if they are not assign a default value
    if hasattr(args, 'cardName') is False:
        args.cardName = "gem-shelf%02d-amc%02d"%(args.shelf,args.slot)
    if hasattr(args, 'stepSize') is False:
        args.stepSize = 1
    if hasattr(args, 'assignXErrors') is False: # For DAC Scan Analysis
        args.assignXErrors = False
    if hasattr(args, 'calFileList') is False: # For DAC Scan Analysis
        args.calFileList = None
    if hasattr(args, 'outfilename') is False: # Name of DAC Scan Analysis File(s)
        args.outfilename = "DACFitData.root" # dacAnalysis(...) will take care of formating in the subfolder
    if hasattr(args, 'printSum') is False: # For DAC Scan Analysis, do not print summary table
        args.printSum = False
    if hasattr(args, 'chConfig') is False: # Text file containing channel configuration
        args.chConfig = None
    if hasattr(args, 'compare') is False: # Just Compare frontend settings?
        args.compare = False
    if hasattr(args, 'filename') is False: # TFile containing channel configuration
        args.filename = None
    if hasattr(args, 'run') is False: # Set chips in run mode on configure?
        args.run = True
    if hasattr(args, 'vt1') is False: # CFG_THR_ARM_DAC (VThreshold1) setting to write for V3 (V2) electronics
        args.vt1 = 100
    if hasattr(args, 'vt1bump') is False: # Value to add to comparator setting
        args.vt1bump = 0
    if hasattr(args, 'vt2') is False: # VThreshold2 value to write if V2 electronics
        args.vt2 = 0
    if hasattr(args, 'vfatConfig') is False: # Text file containing comparator settings
        args.vfatConfig = False
    if hasattr(args, 'zeroChan') is False: # Zero all bits in all channel registers
        args.zeroChan = False

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
    if (not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask)):
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
    if (not vfatBoard.parentOH.parentAMC.getGBTLinkStatus(doReset=True, printSummary=True, ohMask=args.ohMask)):
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
    #from reg_utils.reg_interface.scripts.sca import scaReset
    from reg_utils.reg_interface.common.sca_utils import sca_reset 
    from reg_utils.reg_interface.common.jtag import initJtagRegAddrs
    initJtagRegAddrs()
    for trial in range(0,args.maxIter):
        #scaReset(args)
        sca_reset(args.ohMask)
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
    printYellow("="*20)
    printYellow("Programming FPGA & Checking FPGA Communication")
    printYellow("="*20)

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
    printYellow("="*20)
    printYellow("Checking VFAT Communication")
    printYellow("="*20)

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
    from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_chipIDs = ndict()
    dict_vfat3CalInfo = ndict() # key -> OH number; value -> pandas dataframe
    for ohN in range(nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        vfatBoard.parentOH.link = ohN
        try:
            dict_chipIDs[ohN] = vfatBoard.getAllChipIDs()
        except Exception as e:
            printRed("VFAT communication was not established successfully for OH{0}".format(ohN))
            printYellow("\tTry checking:")
            printYellow("\t\t1. Each of the VFAT FEASTs (FQA, FQB, FQC, and FQD) are properly inserted (make special care to check that the FEAST is *not?* shifted by one pinset)")
            printYellow("\t\t2. The Power Delivered on the VDD (Digital Power) to each VFAT is greater than 1.2V but does not exceed 1.35V")
            printYellow("\t\t3. The Phase Settings written to each VFAT where in the middle of a 'good' window")
            printRed("Conncetivity Testing Failed")
            return

        # Get the calibration info for this detector
        dict_vfat3CalInfo[ohN] = getVFAT3CalInfo(dict_chipIDs[ohN])
        pass

    # All VFATs should work now
    args.vfatmask = 0x0

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
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            vfatBoard.parentOH.link = ohN
            
            # Write IREF
            for idx in dict_vfat3CalInfo[ohN]:
                try:
                    vfatBoard.writeVFAT(
                            dict_vfat3CalInfo['vfatN'][idx],
                            "CFG_IREF",
                            dict_vfat3CalInfo['iref'][idx])
                except Exception as e:
                    printRed("VFAT communication was not established successfully for OH{0} VFAT{1}".format(ohN,dict_vfat3CalInfo['vfatN'][idx]))
                    printRed("Conncetivity Testing Failed")
                    return
                pass

            # Set to Run Mode
            # If time is an issue these two statements could be merged into one
            try:
                vfatBoard.setRunModeAll()
            except Exception as e:
                printRed("VFAT communication was not established successfully for OH{0}".format(ohN))
                printRed("Conncetivity Testing Failed")
                return
            pass

        # DAC Scan
        from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
        from gempython.vfatqc.utils.scanUtils import dacScanAllLinks 
        for dacSelect in maxVfat3DACSize.keys():
            args.dacSelect = dacSelect
            try:
                dacScanAllLinks(args, calTree, vfatBoard)
            except Exception as e:
                printRed("DAC Scan for DAC {0} Failed".format(maxVfat3DACSize[dacSelect]))
                printRed("Conncetivity Testing Failed")
                return
            pass
        pass

    # Analyze DACs
    # =================================================================
    if not args.skipDACScan:
        printYellow("="*20)
        printYellow("Analyzing VFAT3 DAC Scan Data")
        printYellow("="*20)

        # Placeholder, load parameters for ADC calibration from DB FIXME
        # Right now need to rely on someone making the file by hand and placing it in the correct location

        #chamber_config needs to be defined FIXME
        #temporary fix
        from gempython.gemplotting.mapping.chamberInfo import chamber_config

        # Analyze DAC Scan
        from gempython.gemplotting.utils.anautilities import dacAnalysis
        try:
            dict_dacVals = dacAnalysis(args, calTree, chamber_config, scandate=startTime)
        except Exception as e:
            printRed("DAC Scan Analysis Failed")
            printRed("Conncetivity Testing Failed")
            return
        pass
    pass

    # Load DAC Values to Front-End
    # =================================================================
    printYellow("="*20)
    printYellow("Configuring VFAT3's")
    printYellow("="*20)

    from gempython.vfatqc.confChamber import configure

    # Configure
    for ohN in range(nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        #chamber_config needs to be defined FIXME
        #chamber_vfatDACSettings needs to be defined? FIXME
        
        vfatBoard.parentOH.link = ohN
        try:
            configure(args, vfatBoard)
        except Exception as e:
            printRed("Failed to configure OH{0}".format(ohN))
            printRed("Conncetivity Testing Failed")
            return
        pass

    printGreen("All Chambers Configured")

    # Load DAC Values to DB
    # =================================================================
    # Place holder

    # Take Scurve
    # =================================================================
    if not args.skipScurve:
        printYellow("="*20)
        printYellow("Taking a VFAT3 Scurve Scan")
        printYellow("="*20)

        scurveFiles = {}
        from gempython.vfatqc.utils.scanUtils import launchSCurve
        for ohN in range(nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
        
            #chamber_config needs to be defined FIXME
            #scurveFiles[ohN] = $DATA_PATH/chamber_name/scurve/scandate/SCurveData.root

            #Log File
            logFile = "/tmp/scurveLog_ConnectivityTesting_OH{0}.log".format(ohN)

            vfatBoard.parentOH.link = ohN
            try:
                launchSCurve(
                        cardName = args.cardName,
                        debug = args.debug,
                        filename = scurveFiles[ohN],
                        link = ohN,
                        logFile = logFile,
                        vfatmask = args.vfatmask,
                        voltageStepPulse = args.voltageStepPulse)
            except Exception as e:
                printRed("SCurve for OH{0} Failed".format(ohN))
                printRed("Conncetivity Testing Failed")
                return
            pass
        printGreen("All SCurves Completed")
        pass

    # Analyze Scurve
    # =================================================================
    if not args.skipScurve:
        printYellow("="*20)
        printYellow("Analyzing VFAT3 Scurve Scan Data")
        printYellow("="*20)

        # Load CFG_CAL_DAC calibration from DB
        # calDacInfo = ndict()
        # Placeholder FIXME
        
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
                        [scurveFiles[x] for x in range(len(ohList))],
                        [calDacInfo[x]  for x in range(len(ohList))],
                        [deadChan       for x in range(len(ohList))],
                        [isVFAT3        for x in range(len(ohList))]
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

        print("| OH | N_DEAD |")
        print("| -- | ------ |")
        tooManyDeadChan = False
        from gempython.utils.gemlogger import colors
        for ohN,nDeadChan in enumerate(nDeadChanByOH):
            print("| {0} | {1}{2}{3} |".format(ohN,colors.RED if nDeadChan > 3 else colors.GREEN,nDeadChan,colors.ENDC))
            if nDeadChan > 3:
                tooManyDeadChan = True
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
    parser.add_argument("--deadChanCuts",type=str,help="Comma separated pair of integers specifying in fC the scurve width to consider a channel dead")
    parser.add_argument("-d","--debug",action="store_true",dest="debug",help = "Print additional debugging information")
    parser.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-m","--maxIter",type=int,help="Maximum number of iterations steps 1-4 will be attempted before failing (and exiting)",default=5)
    parser.add_argument("-o","--ohMask",type=parseInt,help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered",default=0x1)
    parser.add_argument("--shelf",type=int,help="uTCA shelf number",default=2)
    parser.add_argument("--skipDACScan",action="store_true",help="Do not perform any DAC Scans")
    parser.add_argument("--skipScurve",action="store_true",help="Do not perform any SCurves")
    parser.add_argument("-s","--slot",type=int,help="AMC slot in uTCA shelf",default=5)
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

    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.INFO)

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    testConnectivity(args)

    print("Goodbye")
