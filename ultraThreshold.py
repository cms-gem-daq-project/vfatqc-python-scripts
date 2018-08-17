#!/bin/env python

if __name__ == '__main__':
    """
    Script to take VT1 data using OH ultra scans
    By: Cameron Bravo (c.bravo@cern.ch)
        Jared Sturdy  (sturdy@cern.ch)
        Brian Dorney (brian.l.dorney@cern.ch)
    """
    
    import sys, os, random, time
    from array import array
    from ctypes import *
    
    from gempython.tools.optohybrid_user_functions_uhal import scanmode
    from gempython.tools.vfat_user_functions_xhal import *
    
    from gempython.vfatqc.qcoptions import parser
    
    parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                      help="Specify minimum channel number to scan", metavar="chMin")
    parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                      help="Specify maximum channel number to scan", metavar="chMax")
    parser.add_option("-f", "--filename", type="string", dest="filename", default="VThreshold1Data_Trimmed.root",
                      help="Specify Output Filename", metavar="filename")
    parser.add_option("--perchannel", action="store_true", dest="perchannel",
                      help="Run a per-channel VT1 scan", metavar="perchannel")
    parser.add_option("--trkdata", action="store_true", dest="trkdata",
                      help="Run a per-VFAT VT1 scan using tracking data (default is to use trigger data)", metavar="trkdata")
    parser.add_option("--vt2", type="int", dest="vt2", default=0,
                      help="Specify VT2 to use", metavar="vt2")
    parser.add_option("--zcc", action="store_true", dest="scanZCC",
                      help="V3 Electronics only, scan the threshold on the ZCC instead of the ARM comparator", metavar="scanZCC")
    
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

    # Setup the output TTree
    from gempython.vfatqc.treeStructure import gemTreeStructure
    gemData = gemTreeStructure('thrTree','Tree Holding CMS GEM VThreshold Data')
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
    if options.debug:
        CHAN_MAX = 5
        pass
    
    mask = options.vfatmask
    
    try:
        vfatBoard.setVFATLatencyAll(mask=options.vfatmask, lat=0, debug=options.debug)
        vfatBoard.setRunModeAll(mask, True, options.debug)
        vfatBoard.setVFATThresholdAll(mask=options.vfatmask, vt1=100, vt2=options.vt2, debug=options.debug)
    
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            print "getting trigger source"
            trgSrc = vfatBoard.parentOH.getTriggerSource()
                
        scanReg = "THR_ARM_DAC"
        if vfatBoard.parentOH.parentAMC.fwVersion >= 3:
            vals = vfatBoard.readAllVFATs("CFG_CAL_PHI", mask)
            calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")), range(0,24)))
            
            vals = vfatBoard.readAllVFATs("CFG_PULSE_STRETCH", mask)
            msplvals =  dict(map(lambda slotID: (slotID, vals[slotID]),range(0,24)))
            
            vals = vfatBoard.readAllVFATs("CFG_LATENCY", mask)
            latvals = dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))

            #Store original CFG_SEL_COMP_MODE
            vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", mask)
            selCompVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                range(0,24)))
    
            #Store original CFG_FORCE_EN_ZCC
            vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", mask)
            forceEnZCCVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                range(0,24)))
    
            if options.scanZCC:
                isZCC[0] = 1
    
                #Reset scanReg
                scanReg = "THR_ZCC_DAC"
                
                print "Setting CFG_SEL_COMP_MODE to 0x2 (ZCC Mode)"
                vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE", 0x2, mask)
                vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", mask)
                selCompVals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                    range(0,24)))
    
                print "Forcing the ZCC output to be enabled independent of the ARM comparator"
                vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC", 0x1, mask)
                vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", mask)
                forceEnZCCVals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                    range(0,24)))
            else:
                print "Setting CFG_SEL_COMP_MODE to 0x1 (ARM Mode)"
                vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE", 0x1, mask)
                vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", mask)
                selCompVals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                    range(0,24)))
    
                print "Do not force ZCC output"
                vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC", 0x0, mask)
                vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", mask)
                forceEnZCCVals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                    range(0,24)))
                pass

            chanRegData = getChannelRegisters(vfatBoard,mask)
            vfatIDvals = vfatBoard.getAllChipIDs(mask)
        else:
            vals = vfatBoard.readAllVFATs("CalPhase",   0x0)
            calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")),range(0,24)))
            
            vals = vfatBoard.readAllVFATs("ContReg2",    0x0)    
            msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),range(0,24)))
                    
            vals = vfatBoard.readAllVFATs("ContReg3",    0x0)
            trimRangevals = dict(map(lambda slotID: (slotID, (0x07 & vals[slotID])),range(0,24)))
                            
            vals = vfatBoard.readAllVFATs("Latency",    0x0)
            latvals = dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                                    
            #vfatIDvals = getAllChipIDs(ohboard, options.gtx, 0x0)
            
            vals  = vfatBoard.readAllVFATs("VThreshold2", 0x0)
            vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
                
            vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt1vals[slotID]),range(0,24)))
            pass
    
        if options.perchannel: 
            gemData.mode[0] = scanmode.THRESHCH
            
            # Set Trigger Source for v2b electronics
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                print "setting trigger source"
                vfatBoard.parentOH.setTriggerSource(0x1)

           # Configure TTC
            print "attempting to configure TTC"
            if 0 == vfatBoard.parentOH.parentAMC.configureTTC(pulseDelay=0,L1Ainterval=250,ohN=options.gtx,enable=True):
                print "TTC configured successfully"
            else:
                raise Exception('RPC response was non-zero, TTC configuration failed')
        
            scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
            scanDataSizeNet = scanDataSizeVFAT * 24
            scanData = (c_uint32 * scanDataSizeNet)()
            for chan in range(CHAN_MIN,CHAN_MAX):
                print "Channel #"+str(chan)
            
                # Reset scanReg if needed
                if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                    scanReg = "VThreshold1PerChan"
    
                # Perform the scan
                rpcResp = vfatBoard.parentOH.performCalibrationScan(
                        chan=chan,
                        dacMax=options.scanmax,
                        dacMin=options.scanmin,
                        enableCal=False,
                        mask=options.vfatmask,
                        nevts=options.nevts,
                        outData=scanData,
                        scanReg=scanReg,
                        stepSize=options.stepSize)
    
                if rpcResp != 0:
                    raise Exception('RPC response was non-zero, threshold scan for channel %i failed'%chan)
                
                sys.stdout.flush()
                for vfat in range(0,24):
                    if (mask >> vfat) & 0x1: continue
                    
                    for threshDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                        try:
                            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                                #trimDAC = (0x1f & vfatBoard.readVFAT(vfat,"VFATChannels.ChanReg%d"%(chan)))
                                gemData.fill(
                                        calPhase = calPhasevals[vfat],
                                        l1aTime = options.L1Atime,
                                        latency = latvals[vfat],
                                        mspl = msplvals[vfat],
                                        Nev = options.nevts,
                                        Nhits = (int(scanData[threshDAC] & 0xffffff)), 
                                        #trimDAC = trimDAC,
                                        trimRange = trimRangevals[vfat],
                                        vfatCH = chan,
                                        #vfatID = vfatIDvals[vfat],
                                        vfatN = vfat,
                                        vth = (vt2vals[vfat] - int((scanData[threshDAC] & 0xff000000) >> 24)),
                                        vth1 = (int((scanData[threshDAC] & 0xff000000) >> 24)),
                                        vth2 = vt2vals[vfat]
                                        )
                            else:
                                if vfat == 0:
                                    # what happens if we don't scan from 0 to 255?
                                    vthr = threshDAC
                                else:
                                    # what happens if we don't scan from 0 to 255?
                                    vthr = threshDAC - vfat*scanDataSizeVFAT
                                    pass
                                
                                gemData.fill(
                                        calPhase = calPhasevals[vfat],
                                        l1aTime = options.L1Atime,
                                        latency = latvals[vfat],
                                        mspl = msplvals[vfat],
                                        Nev = (scanData[threshDAC] & 0xffff),
                                        Nhits = ((scanData[threshDAC]>>16) & 0xffff),
                                        trimDAC = chanRegData[chan+vfat*128]['ARM_TRIM_AMPLITUDE'],
                                        trimPolarity = chanRegData[chan+vfat*128]['ARM_TRIM_POLARITY'],
                                        vfatCH = chan,
                                        vfatID = vfatIDvals[vfat],
                                        vfatN = vfat,
                                        vth1 = vthr,
                                        vthr = vthr
                                        )
                        except IndexError:
                            print 'Unable to index data for channel %i'%chan
                            print scanData[threshDAC]
                    pass
                gemData.autoSave()
                pass
    
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                vfatBoard.parentOH.setTriggerSource(trgSrc)
            vfatBoard.parentOH.parentAMC.toggleTTCGen(options.gtx, False)
            pass
        else:
            if not (vfatBoard.parentOH.parentAMC.fwVersion < 3):
                print "For v3 electronics please use the --perchannel option"
                print "Exiting"
                sys.exit(os.EX_USAGE)
    
            if options.trkdata:
                gemData.mode[0] = scanmode.THRESHTRK

                print "setting trigger source"
                vfatBoard.parentOH.setTriggerSource(0x1)
                
                scanReg = "VThreshold1Trk"
                
                # Configure TTC
                print "attempting to configure TTC"
                if 0 == vfatBoard.parentOH.parentAMC.configureTTC(pulseDelay=0,L1Ainterval=250,ohN=options.gtx,enable=True):
                    print "TTC configured successfully"
                else:
                    raise Exception('RPC response was non-zero, TTC configuration failed')
            else:
                gemData.mode[0] = scanmode.THRESHTRG

                scanReg = "VThreshold1"
                pass
    
            scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
            scanDataSizeNet = scanDataSizeVFAT * 24
            scanData = (c_uint32 * scanDataSizeNet)()
            
            # Perform the scan
            rpcResp = vfatBoard.parentOH.performCalibrationScan(
                    chan=0,
                    dacMax=options.scanmax,
                    dacMin=options.scanmin,
                    enableCal=False,
                    mask=options.vfatmask,
                    nevts=options.nevts,
                    outData=scanData,
                    scanReg=scanReg,
                    stepSize=options.stepSize)
    
            if rpcResp != 0:
                raise Exception('RPC response was non-zero, threshold scan failed')
    
            sys.stdout.flush()
            for vfat in range(0,24):
                if (mask >> vfat) & 0x1: continue
                for threshDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT,options.stepSize):
                    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                        gemData.fill(
                                calPhase = calPhasevals[vfat],
                                l1aTime = options.L1Atime,
                                latency = latvals[vfat],
                                mspl = msplvals[vfat],
                                Nev = options.nevts,
                                Nhits = (int(scanData[threshDAC] & 0xffffff)), 
                                trimRange = trimRangevals[vfat],
                                #vfatID = vfatIDvals[vfat],
                                vfatN = vfat,
                                vth = (vt2vals[vfat] - (int((scanData[threshDAC] & 0xff000000) >> 24))),
                                vth1 = (int((scanData[threshDAC] & 0xff000000) >> 24)),
                                vth2 = vt2vals[vfat]
                                )
                    else:
                        if vfat == 0:
                            # what happens if we don't scan from 0 to 255?
                            vthr = threshDAC
                        else:
                            # what happens if we don't scan from 0 to 255?
                            vthr = threshDAC - vfat*scanDataSizeVFAT
                            pass
                        gemData.fill(
                                calPhase = calPhasevals[vfat],
                                l1aTime = options.L1Atime,
                                latency = latvals[vfat],
                                mspl = msplvals[vfat],
                                Nev = (scanData[threshDAC] & 0xffff),
                                Nhits = ((scanData[threshDAC]>>16) & 0xffff),
                                vfatID = vfatIDvals[vfat],
                                vfatN = vfat,
                                vth1 = vthr,
                                vthr = vthr
                                )
                        pass
                    pass
                pass
            gemData.autoSave("SaveSelf")
    
            if options.trkdata:
                if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                    vfatBoard.parentOH.setTriggerSource(trgSrc)
                vfatBoard.parentOH.parentAMC.toggleTTCGen(options.gtx, False)
                pass
            pass
    
        # Place VFATs back in sleep mode
        vfatBoard.setRunModeAll(mask, False, options.debug)
    
        # Return to original comparator settings
        if vfatBoard.parentOH.parentAMC.fwVersion >= 3:
            for key,val in selCompVals_orig.iteritems():
                if (mask >> key) & 0x1: continue
                vfatBoard.writeVFAT(key,"CFG_SEL_COMP_MODE",val)
            for key,val in forceEnZCCVals_orig.iteritems():
                if (mask >> key) & 0x1: continue
                vfatBoard.writeVFAT(key,"CFG_FORCE_EN_ZCC",val)
    
    except Exception as e:
        gemData.autoSave()
        print "An exception occurred", e
    finally:
        myF.cd()
        gemData.write()
        myF.Close()
