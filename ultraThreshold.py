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

#if options.debug:
#    uhal.setLogLevelTo( uhal.LogLevel.INFO )
#else:
#    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')

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

    #trgSrc = getTriggerSource(ohboard,options.gtx)
    if options.perchannel:
        # Configure TTC
        if 0 == vfatBoard.parentOH.parentAMC.ttcGenConf(options.L1Atime, options.pDel):
            print "TTC configured successfully"
        else:
            print "TTC configuration failed"
            sys.exit(os.EX_CONFIG)
        
        #setTriggerSource(ohboard,options.gtx,0x1)
        #mode[0] = scanmode.THRESHCH
        #sendL1A(ohboard, options.gtx, interval=250, number=0)
    
        scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
        scanDataSizeNet = scanDataSizeVFAT * 24
        scanData = (c_uint32 * scanDataSizeNet)()
        for chan in range(CHAN_MIN,CHAN_MAX):
            vfatCH[0] = chan
            print "Channel #"+str(chan)
            #configureScanModule(ohboard, options.gtx, mode[0], mask, channel=scCH,
            #                    scanmin=THRESH_MIN, scanmax=THRESH_MAX,
            #                    numtrigs=int(N_EVENTS),
            #                    useUltra=True, debug=options.debug)
            #printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)

            #startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
            #scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
            rpcResp = vfatBoard.parentOH.genScan(options.nevts, options.gtx,
                                                 options.scanmin,options.scanmax,options.stepSize,
                                                 chan,1,options.vfatmask,"THR_ARM_DAC",scanData)

            if rpcResp != 0:
                print("threshold scan for channel %i failed"%chan)
                sys.exit(os.EX_SOFTWARE)
            
            sys.stdout.flush()
            for vfat in range(0,24):
            	if (mask >> vfat) & 0x1: continue
                vfatN[0] = vfat
                #dataNow      = scanData[i]
                #trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
                for threshDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT,options.stepSize):
                    try:
                        #vth1[0]  = int((dataNow[VC] & 0xff000000) >> 24)
                        #vth[0]   = vth2[0] - vth1[0]
                        #Nhits[0] = int(dataNow[VC] & 0xffffff)
                        if vfat == 0:
                            vth1[0] = threshDAC
                        else:
                            vth1[0] = threshDAC - vfat*scanDataSizeVFAT
                        Nev[0] = scanData[threshDAC] & 0xffff
                        Nhits[0] = (scanData[threshDAC]>>16) & 0xffff
                        #print vfat,chan,threshDAC,vth1[0],Nhits[0],Nev[0]
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

        #setTriggerSource(ohboard,options.gtx,trgSrc)
        #stopLocalT1(ohboard, options.gtx)
        pass
    #else:
    #    if options.trkdata:
    #        setTriggerSource(ohboard,options.gtx,0x1)
    #        mode[0] = scanmode.THRESHTRK
    #        sendL1A(ohboard, options.gtx, interval=250, number=0)
    #    else:
    #        mode[0] = scanmode.THRESHTRG
    #        pass
    #    configureScanModule(ohboard, options.gtx, mode[0], mask,
    #                        scanmin=THRESH_MIN, scanmax=THRESH_MAX,
    #                        numtrigs=int(N_EVENTS),
    #                        useUltra=True, debug=options.debug)
    #    printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)

    #    startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
    #    scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
    #    sys.stdout.flush()
    #    for i in range(0,24):
    #        if (mask >> i) & 0x1: continue
    #        vfatN[0] = i
    #        dataNow      = scanData[i]
    #        trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
    #        for VC in range(THRESH_MAX-THRESH_MIN+1):
    #            vth1[0]  = int((dataNow[VC] & 0xff000000) >> 24)
    #            vth[0]   = vth2[0] - vth1[0]
    #            Nhits[0] = int(dataNow[VC] & 0xffffff)
    #            myT.Fill()
    #            pass
    #        pass
    #    myT.AutoSave("SaveSelf")

    #    if options.trkdata:
    #        setTriggerSource(ohboard,options.gtx,trgSrc)
    #        stopLocalT1(ohboard, options.gtx)
    #        pass
    #    pass

    # Place VFATs back in sleep mode
    #writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)

except Exception as e:
    gemData.autoSave()
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.write()
    myF.Close()
