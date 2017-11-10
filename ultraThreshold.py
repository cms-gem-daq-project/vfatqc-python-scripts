#!/bin/env python
"""
Script to take VT1 data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
    Jared Sturdy  (sturdy@cern.ch)
    Brian Dorney (brian.l.dorney@cern.ch)
"""

import sys, os, random, time
from array import array
from ctypes import *

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

(options, args) = parser.parse_args()

if options.vt2 not in range(256):
    print "Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2)
    exit(1)

remainder = (options.scanmax-options.scanmin+1) % options.stepSize
if remainder != 0:
    options.scanmax = options.scanmax + remainder
    print "extending scanmax to: ", options.scanmax

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')
myT = r.TTree('thrTree','Tree Holding CMS GEM VT1 Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = -1
myT.Branch( 'Nev', Nev, 'Nev/I' )
vth = array( 'i', [ 0 ] )
myT.Branch( 'vth', vth, 'vth/I' )
vth1 = array( 'i', [ 0 ] )
myT.Branch( 'vth1', vth1, 'vth1/I' )
vth2 = array( 'i', [ 0 ] )
myT.Branch( 'vth2', vth2, 'vth2/I' )
vth2[0] = options.vt2
Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
trimRange = array( 'i', [ 0 ] )
myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx
mode = array( 'i', [ 0 ] )
myT.Branch( 'mode', mode, 'mode/I' )
utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import subprocess,datetime,time
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)

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
    if options.perchannel: 
        # Set Trigger Source for v2b electronics
        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            print "setting trigger source"
            vfatBoard.parentOH.setTriggerSource(0x1)
       
       # Configure TTC
        print "attempting to configure TTC"
        if 0 == vfatBoard.parentOH.parentAMC.configureTTC(pulseDelay=0,L1Ainterval=250,ohN=options.gtx,enable=True):
            print "TTC configured successfully"
        else:
            print "TTC configuration failed"
            sys.exit(os.EX_CONFIG)
    
        scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
        scanDataSizeNet = scanDataSizeVFAT * 24
        scanData = (c_uint32 * scanDataSizeNet)()
        for chan in range(CHAN_MIN,CHAN_MAX):
            vfatCH[0] = chan
            print "Channel #"+str(chan)
        
            # Reset scanReg if needed
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                scanReg = "VThreshold1PerChan"

            # Perform the scan
            rpcResp = vfatBoard.parentOH.performCalibrationScan(chan, scanReg, scanData, enableCal=False, nevts=options.nevts, 
                                                                dacMin=options.scanmin, dacMax=options.scanmax, 
                                                                stepSize=options.stepSize, mask=options.vfatmask)

            if rpcResp != 0:
                print("threshold scan for channel %i failed"%chan)
                sys.exit(os.EX_SOFTWARE)
            
            sys.stdout.flush()
            for vfat in range(0,24):
            	if (mask >> vfat) & 0x1: continue
                vfatN[0] = vfat
                if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                    trimRange[0] = (0x07 & vfatBoard.readVFAT(vfat,"ContReg3"))
                
                for threshDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                    try:
                        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                            vth1[0]  = int((scanData[threshDAC] & 0xff000000) >> 24)
                            vth[0]   = vth2[0] - vth1[0]
                            Nev[0] = options.nevts
                            Nhits[0] = int(scanData[threshDAC] & 0xffffff)
                        else:
                            if vfat == 0:
                                # what happens if we don't scan from 0 to 255?
                                vth1[0] = threshDAC
                            else:
                                # what happens if we don't scan from 0 to 255?
                                vth1[0] = threshDAC - vfat*scanDataSizeVFAT
                            Nev[0] = scanData[threshDAC] & 0xffff
                            Nhits[0] = (scanData[threshDAC]>>16) & 0xffff
                    except IndexError:
                        print 'Unable to index data for channel %i'%chan
                        print scanData[threshDAC]
                        vth1[0]  = -99
                        Nhits[0] = -99
                    finally:
                        myT.Fill()
                pass
            gemData.autoSave()
            pass

        if vfatBoard.parentOH.parentAMC.fwVersion < 3:
            vfatBoard.parentOH.setTriggerSource(trgSrc)
        vfatBoard.parentOH.parentAMC.toggleTTC(options.gtx, False)
        pass
    else:
        if not (vfatBoard.parentOH.parentAMC.fwVersion < 3):
            print "For v3 electronics please use the --perchannel option"
            print "Exiting"
            sys.exit(os.EX_USAGE)

        if options.trkdata:
            print "setting trigger source"
            vfatBoard.parentOH.setTriggerSource(0x1)
            
            scanReg = "VThreshold1Trk"
            
            # Configure TTC
            print "attempting to configure TTC"
            if 0 == vfatBoard.parentOH.parentAMC.configureTTC(pulseDelay=0,L1Ainterval=250,ohN=options.gtx,enable=True):
                print "TTC configured successfully"
            else:
                print "TTC configuration failed"
                sys.exit(os.EX_CONFIG)
        else:
            scanReg = "VThreshold1"
            pass

        scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
        scanDataSizeNet = scanDataSizeVFAT * 24
        scanData = (c_uint32 * scanDataSizeNet)()
        
        # Perform the scan
        rpcResp = vfatBoard.parentOH.performCalibrationScan(0, scanReg, scanData, nevts=options.nevts, 
                                                            dacMin=options.scanmin, dacMax=options.scanmax, 
                                                            stepSize=options.stepSize, mask=options.vfatmask)

        if rpcResp != 0:
            print("threshold scan failed")
            sys.exit(os.EX_SOFTWARE)

        sys.stdout.flush()
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            vfatN[0] = vfat
            trimRange[0] = (0x07 & vfatBoard.readVFAT(vfat,"ContReg3"))
            for threshDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT,options.stepSize):
                if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                    vth1[0]  = int((scanData[threshDAC] & 0xff000000) >> 24)
                    vth[0]   = vth2[0] - vth1[0]
                    Nev[0] = options.nevts
                    Nhits[0] = int(scanData[threshDAC] & 0xffffff)
                else:
                    if vfat == 0:
                        # what happens if we don't scan from 0 to 255?
                        vth1[0] = threshDAC
                    else:
                        # what happens if we don't scan from 0 to 255?
                        vth1[0] = threshDAC - vfat*scanDataSizeVFAT
                    Nev[0] = scanData[threshDAC] & 0xffff
                    Nhits[0] = (scanData[threshDAC]>>16) & 0xffff
                myT.Fill()
                pass
            pass
        myT.AutoSave("SaveSelf")

        if options.trkdata:
            if vfatBoard.parentOH.parentAMC.fwVersion < 3:
                vfatBoard.parentOH.setTriggerSource(trgSrc)
            vfatBoard.parentOH.parentAMC.toggleTTC(options.gtx, False)
            pass
        pass

    # Place VFATs back in sleep mode
    vfatBoard.setRunModeAll(mask, False, options.debug)

except Exception as e:
    gemData.autoSave()
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.write()
    myF.Close()
