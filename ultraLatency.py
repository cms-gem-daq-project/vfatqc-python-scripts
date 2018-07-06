#!/bin/env python

if __name__ == '__main__':
    """
    Script to take latency data using OH ultra scans
    By: Jared Sturdy  (sturdy@cern.ch)
        Cameron Bravo (c.bravo@cern.ch)
        Brian Dorney (brian.l.dorney@cern.ch)
    """
    
    import sys, os, random, time
    from array import array
    from ctypes import *
    
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.tools.vfat_user_functions_uhal import * #remove this later after making it so amc13 communication doesn't spit bullshit messages
    from gempython.tools.optohybrid_user_functions_uhal import scanmode
    
    from gempython.vfatqc.qcoptions import parser
    
    parser.add_option("--amc13local", action="store_true", dest="amc13local",
                      help="Set up for using AMC13 local trigger generator", metavar="amc13local")
    parser.add_option("--fakeTTC", action="store_true", dest="fakeTTC",
                      help="Set up for using AMC13 local TTC generator", metavar="fakeTTC")
    parser.add_option("--filename", type="string", dest="filename", default="LatencyScanData.root",
                      help="Specify Output Filename", metavar="filename")
    parser.add_option("--internal", action="store_true", dest="internal",
                      help="Run a latency scan using the internal calibration pulse", metavar="internal")
    parser.add_option("--randoms", type="int", default=0, dest="randoms",
                      help="Set up for using AMC13 local trigger generator to generate random triggers with rate specified",
                      metavar="randoms")
    parser.add_option("--t3trig", action="store_true", dest="t3trig",
                      help="Set up for using AMC13 T3 trigger input", metavar="t3trig")
    parser.add_option("--throttle", type="int", default=0, dest="throttle",
                      help="factor by which to throttle the input L1A rate, e.g. new trig rate = L1A rate / throttle", metavar="throttle")
    parser.add_option("--vcal", type="int", dest="vcal",
                      help="Height of CalPulse in DAC units for all VFATs", metavar="vcal", default=250)
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    parser.add_option("--vt2", type="int", dest="vt2",
                      help="VThreshold2 DAC value for all VFATs (v2b electronics only)", metavar="vt2", default=0)
    
    parser.set_defaults(scanmin=153,scanmax=172,nevts=500)
    (options, args) = parser.parse_args()
    
    remainder = (options.scanmax-options.scanmin+1) % options.stepSize
    if remainder != 0:
        options.scanmax = options.scanmax + remainder
        print "extending scanmax to: ", options.scanmax
    
    if options.debug:
        uhal.setLogLevelTo(uhal.LogLevel.INFO)
    else:
        uhal.setLogLevelTo(uhal.LogLevel.ERROR)
    
    from ROOT import TFile,TTree
    filename = options.filename
    myF = TFile(filename,'recreate')
    
    import subprocess,datetime,time
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print(startTime)
    Date = startTime
    
    # Track the current pulse
    isCurrentPulse = (not options.voltageStepPulse)
    
    # Setup the output TTree
    from gempython.vfatqc.treeStructure import gemTreeStructure
    gemData = gemTreeStructure('latTree','Tree Holding CMS GEM Latency Data',scanmode.LATENCY)
    gemData.setDefaults(options, int(time.time()))
    
    import amc13
    connection_file = "%s/connections.xml"%(os.getenv("GEM_ADDRESS_TABLE_PATH"))
    amc13base  = "gem.shelf%02d.amc13"%(options.shelf)
    amc13board = amc13.AMC13(connection_file,"%s.T1"%(amc13base),"%s.T2"%(amc13base))
    
    # Open rpc connection to hw
    if options.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    vfatBoard = HwVFAT(options.cardName, options.gtx, options.debug)
    print 'opened connection'
    
    # Check options
    from gempython.vfatqc.qcutilities import inputOptionsValid
    if not inputOptionsValid(options, vfatBoard.parentOH.parentAMC.fwVersion):
        exit(os.EX_USAGE)
        pass
    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
        if options.scanmin not in range(256) or options.scanmax not in range(256) or not (options.scanmax > options.scanmin):
            print("Invalid scan parameters specified [min,max] = [%d,%d]"%(options.scanmin,options.scanmax))
            print("Scan parameters must be in range [0,255] and min < max")
            exit(1)
            pass
    else:
        if options.scanmin not in range(1025) or options.scanmax not in range(1025) or not (options.scanmax > options.scanmin):
            print("Invalid scan parameters specified [min,max] = [%d,%d]"%(options.scanmin,options.scanmax))
            print("Scan parameters must be in range [0,1024] and min < max")
            exit(1)
            pass
    
    mask = options.vfatmask
    
    try:
        vfatBoard.setRunModeAll(mask, True, options.debug)
        vfatBoard.setVFATMSPLAll(mask, options.MSPL, options.debug)
        
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            vfatBoard.writeAllVFATs("VThreshold2", options.vt2, mask)
    
            vals = vfatBoard.readAllVFATs("CalPhase",   0x0)
            calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")),
                                range(0,24)))
            vals = vfatBoard.readAllVFATs("ContReg2",    0x0)
            msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),
                                range(0,24)))
            vals = vfatBoard.readAllVFATs("ContReg3",    0x0)
            trimRangevals = dict(map(lambda slotID: (slotID, (0x07 & vals[slotID])),
                                range(0,24)))
            #vfatIDvals = getAllChipIDs(ohboard, options.gtx, 0x0)
            vals  = vfatBoard.readAllVFATs("VThreshold1", 0x0)
            vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                                range(0,24)))
            vals  = vfatBoard.readAllVFATs("VThreshold2", 0x0)
            vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                                range(0,24)))
            vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt1vals[slotID]),
                                range(0,24)))
        else:
            vals  = vfatBoard.readAllVFATs("CFG_THR_ARM_DAC", mask)
            vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                                range(0,24)))
            vals = vfatBoard.readAllVFATs("CFG_PULSE_STRETCH", mask)
            msplvals =  dict(map(lambda slotID: (slotID, vals[slotID]),
                                 range(0,24)))
    
        # Stop triggers
        vfatBoard.parentOH.parentAMC.blockL1A()
        amc13board.enableLocalL1A(False)
        amc13board.resetCounters()
    
        # Check to see if an ultra scan is already running
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            scanBase = "GEM_AMC.OH.OH%d.ScanController.ULTRA"%(options.gtx)
            if (vfatBoard.parentOH.parentAMC.readRegister("%s.MONITOR.STATUS"%(scanBase)) > 0):
                print("Scan was already running, resetting module")
                vfatBoard.parentOH.parentAMC.writeRegister("%s.RESET"%(scanBase),0x1)
                time.sleep(0.1)
                pass
        
        amc13nL1A = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
        amcnL1A = vfatBoard.parentOH.parentAMC.getL1ACount()
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            ohnL1A = vfatBoard.parentOH.getL1ACount()
        
        print "Initial L1A counts:"
        print "AMC13: %s"%(amc13nL1A)
        print "AMC: %s"%(amcnL1A)
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            print "OH%s: %s"%(options.gtx,ohnL1A)
        sys.stdout.flush()
    
        scanChan=128
        enableCalPulse=False
        if options.internal:
            enableCalPulse=True
            scanChan=0
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                vfatBoard.parentOH.setTriggerSource(0x1)
            
            print "stopping cal pulse to all channels"
            vfatBoard.stopCalPulses(mask, 0, 128)
            
            print "Setting channel %i to calpulse"%(scanChan)
            vfatBoard.setSpecificChannelAllRegisters(chan=scanChan, chMask=0, pulse=1, trimARM=0, vfatMask=mask)
            vfatBoard.setVFATCalHeightAll(mask, options.vcal, currentPulse=isCurrentPulse)
    
            # Configure TTC
            print "attempting to configure TTC"
            if 0 == vfatBoard.parentOH.parentAMC.configureTTC(options.pDel,options.L1Atime,options.gtx,1,0,0,True):
                print "TTC configured successfully"
                vfatBoard.parentOH.parentAMC.getTTCStatus(options.gtx,True)
            else:
                raise Exception('RPC response was non-zero, TTC configuration failed')
        else:
            if options.amc13local:
                amcMask = amc13board.parseInputEnableList("%s"%(options.slot), True)
                amc13board.reset(amc13board.Board.T1)
                amc13board.resetCounters()
                amc13board.resetDAQ()
                if options.fakeTTC:
                    amc13board.localTtcSignalEnable(options.fakeTTC)
                    pass
                amc13board.AMCInputEnable(amcMask)
                amc13board.startRun()
                # rate should be desired rate * 16
                # mode may be: 0(per-orbit), 1(per-BX), 2(random)
                # configureLocalL1A(ena, mode, burst, rate, rules)
                if options.randoms > 0:
                    amc13board.configureLocalL1A(True, 0, 1, 1, 0) # per-orbit
                    pass
                if options.t3trig:
                    amc13board.write(amc13board.Board.T1, 'CONF.TTC.T3_TRIG', 0x1)
                    pass
                # to prevent trigger blocking
                amc13board.fakeDataEnable(True)
                # disable the event builder?
                # amc13board.write(amc13board.Board.T1, 'CONF.DIAG.DISABLE_EVB', 0x1)
                #amc13board.enableLocalL1A(True)
                if options.randoms > 0:
                    amc13board.startContinuousL1A()
                    pass
                pass
            
            print "attempting to configure TTC"
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                vfatBoard.parentOH.setTriggerSource(0x5) # GBT, 0x0 for GTX
            print "TTC configured successfully"
            pass
    
        # Throttle the trigger if requested
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            vfatBoard.parentOH.setTriggerThrottle(options.throttle)
        sys.stdout.flush()
        
        scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
        scanDataSizeNet = scanDataSizeVFAT * 24
        scanData = (c_uint32 * scanDataSizeNet)()
            
        # Determine the scanReg
        scanReg = "LATENCY"
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            scanReg = "Latency"
     
        # Perform the scan
        if options.internal:
            print("Starting scan for channel %i; pulseDelay: %i; L1Atime: %i"%(scanChan, options.pDel, options.L1Atime))
        else:
            print("Starting scan")
        # Not sure I understand why it has to be scanChan+1 below...
        amc13board.enableLocalL1A(True)
        vfatBoard.parentOH.parentAMC.enableL1A()
        rpcResp = vfatBoard.parentOH.performCalibrationScan(scanChan, scanReg, scanData, enableCal=enableCalPulse, currentPulse=isCurrentPulse, nevts=options.nevts, 
                                                            dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, 
                                                            mask=options.vfatmask, useExtTrig=(not options.internal))
    
        if rpcResp != 0:
            raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')
        print("Done scanning, processing output")
        
        print "Final L1A counts:"
        amc13board.enableLocalL1A(False)
        vfatBoard.parentOH.parentAMC.blockL1A()
        amc13nL1Af = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
        amcnL1Af = vfatBoard.parentOH.parentAMC.getL1ACount()
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            ohnL1Af = vfatBoard.parentOH.getL1ACount()
        print "AMC13: %s, difference %s"%(amc13nL1Af,amc13nL1Af-amc13nL1A)
        print "AMC: %s, difference %s"%(amcnL1Af,amcnL1Af-amcnL1A)
        
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            print "OH%s: %s, difference %s"%(options.gtx,ohnL1Af,ohnL1Af-ohnL1A)
    
        print("Information on CRC packets")
        print("\tActually still needs to be implemented (oops) - Brian")
        # this is the way to do this for v2b
        #for i in range(24):
        #  print "Total number of CRC packets for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)) + readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.VALID.VFAT%d"%(options.gtx,i)))
        #for i in range(24):
        #  print "Number of CRC errors for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)))
        # for v3 evaldas says I can count number of good & bad CRC eventss w/DAQ_MONITPR as well as number of L1As received by the CTP7 and forwarded to the VFATs with GEM_AMC.TTC.CMD_COUNTERS.L1A
    
        #amc13board.enableLocalL1A(True)
        sys.stdout.flush()
        print("parsing scan data")
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            if options.debug:
                sys.stdout.flush()
                pass
            for latReg in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                try:
                    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                        gemData.fill(
                                calPhase = calPhasevals[vfat],
                                latency = int((scanData[latReg] & 0xff000000) >> 24),
                                mspl = msplvals[vfat],
                                Nhits = int(scanData[latReg] & 0xffffff),
                                trimRange = trimRangevals[vfat],
                                #vfatID = vfatIDvals[vfat],
                                vfatN = vfat,
                                vth = vthvals[vfat],
                                vth1 = vt1vals[vfat],
                                vth2 = vt2vals[vfat]
                                )
                    else:
                        gemData.fill(
                                isCurrentPulse = isCurrentPulse,
                                latency = (options.scanmin + (latReg - vfat*scanDataSizeVFAT) * options.stepSize), 
                                mspl = msplvals[vfat],
                                Nev = (scanData[latReg] & 0xffff),
                                Nhits = ((scanData[latReg]>>16) & 0xffff),
                                #vfatID = vfatIDvals[vfat],
                                vfatN = vfat,
                                vth1 = vt1vals[vfat]
                                )
                        pass
    
                except IndexError:
                    print 'Unable to index data for channel %i'%chan
                    print scanData[latReg]
                finally:
                    if options.debug:
                        print "vfat%i; lat %i; Nev %i; Nhits %i"%(
                                gemData.vfatN[0],
                                gemData.latency[0],
                                gemData.Nev[0],
                                gemData.Nhits[0])
                pass
            pass
        gemData.autoSave("SaveSelf")
    
        vfatBoard.setRunModeAll(mask, False, options.debug)
        if options.internal:
            vfatBoard.parentOH.parentAMC.toggleTTCGen(options.gtx, False)
            pass
        elif options.amc13local:
            amc13board.stopContinuousL1A()
            amc13board.fakeDataEnable(False)
            pass
    except Exception as e:
        gemData.autoSave()
        print("An exception occurred", e)
    finally:
        myF.cd()
        gemData.write()
        myF.Close()
