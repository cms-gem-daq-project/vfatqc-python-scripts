#!/bin/env python

if __name__ == '__main__':
    """
    Script to take Scurve data using OH ultra scans
    By: Cameron Bravo (c.bravo@cern.ch) and Brian Dorney (brian.l.dorney@cern.ch)
    """
    
    from array import array
    from ctypes import *
    from gempython.tools.optohybrid_user_functions_uhal import scanmode
    from gempython.tools.vfat_user_functions_xhal import *
    
    from gempython.vfatqc.qcoptions import parser
    
    import os, sys
    
    parser.add_option("--CalPhase", type="int", dest = "CalPhase", default = 0,
                      help="Specify CalPhase. Must be in range 0-8", metavar="CalPhase")
    parser.add_option("--calSF", type="int", dest = "calSF", default = 0,
                      help="V3 electroncis only. Value of the CFG_CAL_FS register", metavar="calSF")
    parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                      help="Specify minimum channel number to scan", metavar="chMin")
    parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                      help="Specify maximum channel number to scan", metavar="chMax")
    parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                      help="Specify Output Filename", metavar="filename")
    parser.add_option("--latency", type="int", dest = "latency", default = 37,
                      help="Specify Latency", metavar="latency")
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="V3 electronics only. Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    (options, args) = parser.parse_args()
    
    remainder = (options.scanmax-options.scanmin+1) % options.stepSize
    if remainder != 0:
        options.scanmax = options.scanmax + remainder
        print "extending scanmax to: ", options.scanmax
    
    import ROOT as r
    filename = options.filename
    myF = r.TFile(filename,'recreate')
    
    import subprocess,datetime,time
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print startTime
    Date = startTime

    # Track the current pulse
    isCurrentPulse = (not options.voltageStepPulse)

    # Setup the output TTree
    from gempython.vfatqc.treeStructure import gemTreeStructure
    gemData = gemTreeStructure('scurveTree','Tree Holding CMS GEM SCurve Data',scanmode.SCURVE)
    gemData.setDefaults(options, int(time.time()))

    # Open rpc connection to hw
    if options.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    vfatBoard = HwVFAT(options.cardName, options.gtx, options.debug)
    print 'opened connection'

    # Check options
    from gempython.vfatqc.qcutilities import getChannelRegisters, inputOptionsValid
    if not inputOptionsValid(options, vfatBoard.parentOH.parentAMC.fwVersion):
        exit(os.EX_USAGE)
        pass
    if options.scanmin not in range(256) or options.scanmax not in range(256) or not (options.scanmax > options.scanmin):
        print("Invalid scan parameters specified [min,max] = [%d,%d]"%(options.scanmin,options.scanmax))
        print("Scan parameters must be in range [0,255] and min < max")
        exit(1)
        pass

    CHAN_MIN = options.chMin
    CHAN_MAX = options.chMax + 1
    
    mask = options.vfatmask
    
    try:
        # Set Trigger Source for v2b electronics
        print "setting trigger source"
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            vfatBoard.parentOH.setTriggerSource(0x1)
            print("OH%i: Trigger Source %i"%(vfatBoard.parentOH.link,vfatBoard.parentOH.getTriggerSource()))
    
        # Configure TTC
        print "attempting to configure TTC"
        if 0 == vfatBoard.parentOH.parentAMC.configureTTC(options.pDel,options.L1Atime,options.gtx,1,0,0,True):
            print "TTC configured successfully"
            vfatBoard.parentOH.parentAMC.getTTCStatus(options.gtx,True)
        else:
            raise Exception('RPC response was non-zero, TTC configuration failed')
    
        vfatBoard.setVFATLatencyAll(mask=options.vfatmask, lat=options.latency, debug=options.debug)
        vfatBoard.setRunModeAll(mask, True, options.debug)
        vfatBoard.setVFATMSPLAll(mask, options.MSPL, options.debug)
        vfatBoard.setVFATCalPhaseAll(mask, 0xff >> (8 - options.CalPhase), options.debug)
   
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            vals = vfatBoard.readAllVFATs("CalPhase",   0x0)
            calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")), range(0,24)))
                
            vals = vfatBoard.readAllVFATs("ContReg2",    0x0)
            msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),range(0,24)))
                
            vals = vfatBoard.readAllVFATs("ContReg3",    0x0)
            trimRangevals = dict(map(lambda slotID: (slotID, (0x07 & vals[slotID])),range(0,24)))
                
            vals = vfatBoard.readAllVFATs("Latency",    0x0)
            latvals = dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                
            #vfatIDvals = getAllChipIDs(ohboard, options.gtx, 0x0)
            
            vals  = vfatBoard.readAllVFATs("VThreshold1", 0x0)
            vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                
            vals  = vfatBoard.readAllVFATs("VThreshold2", 0x0)
            vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                
            vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt1vals[slotID]),range(0,24)))
        else:
            vals = vfatBoard.readAllVFATs("CFG_CAL_PHI",   mask)
            calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")), range(0,24)))
        
            vals = vfatBoard.readAllVFATs("CFG_PULSE_STRETCH", mask)
            msplvals =  dict(map(lambda slotID: (slotID, vals[slotID]),range(0,24)))
            
            vals = vfatBoard.readAllVFATs("CFG_LATENCY",    mask)
            latvals = dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                
            vals  = vfatBoard.readAllVFATs("CFG_THR_ARM_DAC", mask)
            vthrvals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
            
            chanRegData = getChannelRegisters(vfatBoard,mask)
            vfatIDvals = vfatBoard.getAllChipIDs(0x0)

            pass

        # Make sure no channels are receiving a cal pulse
        # This needs to be done on the CTP7 otherwise it takes an hour...
        print "stopping cal pulse to all channels"
        vfatBoard.stopCalPulses(mask, CHAN_MIN, CHAN_MAX)
    
        scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
        scanDataSizeNet = scanDataSizeVFAT * 24
        scanData = (c_uint32 * scanDataSizeNet)()
        for chan in range(CHAN_MIN,CHAN_MAX):
            print "Channel #"+str(chan)
            
            # Determine the scanReg
            scanReg = "CAL_DAC"
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                scanReg = "VCal"
                
            # Perform the scan
            if options.debug: 
                print("Starting scan; pulseDelay: %i; L1Atime: %i; Latency: %i"%(options.pDel, options.L1Atime, options.latency))
            rpcResp = vfatBoard.parentOH.performCalibrationScan(
                    chan=chan,
                    calSF=options.calSF,
                    currentPulse=isCurrentPulse,
                    dacMax=options.scanmax,
                    dacMin=options.scanmin,
                    enableCal=True,
                    mask=options.vfatmask,
                    nevts=options.nevts,
                    outData=scanData,
                    stepSize=options.stepSize,
                    scanReg=scanReg)
    
            if rpcResp != 0:
                raise Exception('RPC response was non-zero, scurve for channel %i failed'%chan)
            
            for vfat in range(0,24):
                if (mask >> vfat) & 0x1: continue
                for vcalDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                    try:
                        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                            #trimDAC = (0x1f & vfatBoard.readVFAT(vfat,"VFATChannels.ChanReg%d"%(chan)))
                            gemData.fill(
                                    calPhase = calPhasevals[vfat],
                                    l1aTime = options.L1Atime,
                                    latency = latvals[vfat],
                                    mspl = msplvals[vfat],
                                    Nev = options.nevts,
                                    Nhits = int(scanData[vcalDAC] & 0xffffff), 
                                    pDel = options.pDel,
                                    #trimDAC = trimDAC,
                                    trimRange = trimRangevals[vfat],
                                    vcal = int((scanData[vcalDAC] & 0xff000000) >> 24),
                                    vfatCH = chan,
                                    #vfatID = vfatIDvals[vfat],
                                    vfatN = vfat,
                                    vth = vthvals[vfat],
                                    vth1 = vt1vals[vfat],
                                    vth2 = vt2vals[vfat],
                                    vthr = vt1vals[vfat]
                                    )
                        else:
                            gemData.fill(
                                    calPhase = calPhasevals[vfat],
                                    isCurrentPulse = isCurrentPulse,
                                    l1aTime = options.L1Atime,
                                    latency = latvals[vfat],
                                    mspl = msplvals[vfat],
                                    Nev = (scanData[vcalDAC] & 0xffff),
                                    Nhits = ((scanData[vcalDAC]>>16) & 0xffff),
                                    pDel = options.pDel,
                                    trimDAC = chanRegData[chan+vfat*128]['ARM_TRIM_AMPLITUDE'],
                                    trimPolarity = chanRegData[chan+vfat*128]['ARM_TRIM_POLARITY'],
                                    vcal = (options.scanmin + (vcalDAC - vfat*scanDataSizeVFAT) * options.stepSize),
                                    vfatCH = chan,
                                    vfatID = vfatIDvals[vfat],
                                    vfatN = vfat,
                                    vthr = vthrvals[vfat]
                                    )
                            pass

                    except IndexError:
                        print 'Unable to index data for channel %i'%chan
                        print scanData[vcalDAC]
                    finally:
                        if options.debug:
                            print "vfat%i; vcal %i; Nev %i; Nhits %i"%(
                                    gemData.vfatN[0],
                                    gemData.vcal[0],
                                    gemData.Nev[0],
                                    gemData.Nhits[0])
                            pass
                        pass
            gemData.autoSave("SaveSelf")
            sys.stdout.flush()
            pass
        
        vfatBoard.parentOH.parentAMC.toggleTTCGen(options.gtx, False)
        vfatBoard.setRunModeAll(mask, False, options.debug)
    except Exception as e:
        gemData.autoSave()
        print "An exception occurred", e
    finally:
        myF.cd()
        gemData.write()
        myF.Close()
