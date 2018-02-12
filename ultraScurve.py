#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch) and Brian Dorney (brian.l.dorney@cern.ch)
"""

from array import array
from ctypes import *
from gempython.tools.vfat_user_functions_xhal import *

from gempython.vfatqc.qcoptions import parser

import os, sys

parser.add_option("--CalPhase", type="int", dest = "CalPhase", default = 0,
                  help="Specify CalPhase. Must be in range 0-8", metavar="CalPhase")
parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                  help="Specify minimum channel number to scan", metavar="chMin")
parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                  help="Specify maximum channel number to scan", metavar="chMax")
parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--latency", type="int", dest = "latency", default = 37,
                  help="Specify Latency", metavar="latency")
parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                  help="Calibration Module is set to use voltage step pulsing instead of default
                        current pulse injection", metavar="voltageStepPulse")

(options, args) = parser.parse_args()

if options.MSPL < 1 or options.MSPL > 8:
    print 'MSPL must be in the range 1-8'
    exit(os.EX_USAGE)
    pass
if not (0 <= options.chMin <= options.chMax < 128):
    print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
    exit(os.EX_USAGE)
    pass

remainder = (options.scanmax-options.scanmin+1) % options.stepSize
if remainder != 0:
    options.scanmax = options.scanmax + remainder
    print "extending scanmax to: ", options.scanmax

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')
myT = r.TTree('scurveTree','Tree Holding CMS GEM SCurve Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = -1
myT.Branch( 'Nev', Nev, 'Nev/I' )

vcal = array( 'i', [ 0 ] )
myT.Branch( 'vcal', vcal, 'vcal/I' )

Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )

vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )

vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )

trimRange = array( 'i', [ 0 ] )
myT.Branch( 'trimRange', trimRange, 'trimRange/I' )

vthr = array( 'i', [ 0 ] )
myT.Branch( 'vthr', vthr, 'vthr/I' )

trimDAC = array( 'i', [ 0 ] )
myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )

l1aTime = array( 'i', [ 0 ] )
myT.Branch( 'l1aTime', l1aTime, 'l1aTime/I' )
l1aTime[0] = options.L1Atime

mspl = array( 'i', [ 0 ] )
myT.Branch( 'mspl', mspl, 'mspl/I' )
mspl[0] = options.MSPL

latency = array( 'i', [ 0 ] )
myT.Branch( 'latency', latency, 'latency/I' )
latency[0] = options.latency

pDel = array( 'i', [ 0 ] )
myT.Branch( 'pDel', pDel, 'pDel/I' )
pDel[0] = options.pDel

calPhase = array( 'i', [ 0 ] )
myT.Branch( 'calPhase', calPhase, 'calPhase/I' )
calPhase[0] = options.CalPhase

isCurrentPulse = array( 'i', [ 0 ] )
myT.Branch( 'isCurrentPulse', isCurrentPulse, 'isCurrentPulse/I')
isCurrentPulse[0] = not options.voltageStepPulse

link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx

utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import subprocess,datetime,time
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)

if vfatBoard.parentOH.parentAMC.fwVersion < 3:
    if options.CalPhase < 0 or options.CalPhase > 8:
        print 'CalPhase must be in the range 0-8'
        exit(os.EX_USAGE)
        pass
else:
    if options.CalPhase < 0 or options.CalPhase > 7:
        print 'CalPhase must be in the range 0-7'
        exit(os.EX_USAGE)
        pass

CHAN_MIN = options.chMin
CHAN_MAX = options.chMax + 1
#if options.debug:
#    CHAN_MAX = 5
#    pass

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

    # Make sure no channels are receiving a cal pulse
    # This needs to be done on the CTP7 otherwise it takes an hour...
    print "stopping cal pulse to all channels"
    vfatBoard.stopCalPulses(mask, CHAN_MIN, CHAN_MAX)

    scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
    scanDataSizeNet = scanDataSizeVFAT * 24
    scanData = (c_uint32 * scanDataSizeNet)()
    for chan in range(CHAN_MIN,CHAN_MAX):
        vfatCH[0] = chan
        print "Channel #"+str(chan)
        
        # Determine the scanReg
        scanReg = "CAL_DAC"
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            scanReg = "VCal"
            
        # Perform the scan
        if options.debug: 
            print("Starting scan; pulseDelay: %i; L1Atime: %i; Latency: %i"%(options.pDel, options.L1Atime, options.latency))
        rpcResp = vfatBoard.parentOH.performCalibrationScan(chan, scanReg, scanData, enableCal=True, currentPulse=isCurrentPulse[0], 
                                                            nevts=options.nevts, 
                                                            dacMin=options.scanmin, dacMax=options.scanmax, 
                                                            stepSize=options.stepSize, mask=options.vfatmask)

        if rpcResp != 0:
            raise Exception('RPC response was non-zero, scurve for channel %i failed'%chan)
        
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            vfatN[0] = vfat
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                trimRange[0] = (0x07 & vfatBoard.readVFAT(vfat,"ContReg3"))
                trimDAC[0]   = (0x1f & vfatBoard.readVFAT(vfat,"VFATChannels.ChanReg%d"%(chan)))
                vthr[0]      = (0xff & vfatBoard.readVFAT(vfat,"VThreshold1"))
            else:
                trimDAC[0]   = (0x3f & vfatBoard.readVFAT(vfat,"VFAT_CHANNELS.CHANNEL%d.ARM_TRIM_AMPLITUDE"%(chan)))
                vthr[0]      = (0xff & vfatBoard.readVFAT(vfat,"CFG_THR_ARM_DAC"))
            
            for vcalDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                try:
                    # Set Nev, Nhits & vcal
                    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                        vcal[0]  = int((scanData[vcalDAC] & 0xff000000) >> 24)
                        Nev[0] = options.nevts
                        Nhits[0] = int(scanData[vcalDAC] & 0xffffff)
                    else:
                        #if vfat == 0:
                        #    vcal[0] = scanDataSizeVFAT - vcalDAC
                        #else:
                        #    vcal[0] = (vfat+1)*scanDataSizeVFAT - vcalDAC
                        vcal[0] = options.scanmin + (vcalDAC - vfat*scanDataSizeVFAT) * options.stepSize
                        Nev[0] = scanData[vcalDAC] & 0xffff
                        Nhits[0] = (scanData[vcalDAC]>>16) & 0xffff
                except IndexError:
                    print 'Unable to index data for channel %i'%chan
                    print scanData[vcalDAC]
                    vcal[0]  = -99
                    Nhits[0] = -99
                finally:
                    if options.debug:
                        print "vfat%i; vcal %i; Nev %i; Nhits %i"%(vfatN[0],vcal[0],Nev[0],Nhits[0])
                    myT.Fill()
        myT.AutoSave("SaveSelf")
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
