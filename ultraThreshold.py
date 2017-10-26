#!/bin/env python
"""
Script to take VT1 data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
    Jared Sturdy  (sturdy@cern.ch)

Modified By:
    Brian Dorney (brian.l.dorney@cern.ch)
"""

import sys, os, random, time
from array import array

from gempython.tools.optohybrid_user_functions_uhal import *
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("--vt2", type="int", dest="vt2", default=0,
                  help="Specify VT2 to use", metavar="vt2")
parser.add_option("-f", "--filename", type="string", dest="filename", default="VThreshold1Data_Trimmed.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--perchannel", action="store_true", dest="perchannel",
                  help="Run a per-channel VT1 scan", metavar="perchannel")
parser.add_option("--trkdata", action="store_true", dest="trkdata",
                  help="Run a per-VFAT VT1 scan using tracking data (default is to use trigger data)", metavar="trkdata")

(options, args) = parser.parse_args()

if options.vt2 not in range(256):
    print "Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2)
    exit(1)

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.INFO )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')


# Setup the output TTree
from treeStructure import gemTreeStructure
gemData = gemTreeStructure('thrTree','Tree Holding CMS GEM VT1 Data')
gemData.link[0] = options.gtx
gemData.Nev[0] = options.nevts
gemData.vth2[0] = options.vt2

import subprocess,datetime,time
gemData.utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

from gempython.tools.amc_user_functions_uhal import *
amcBoard = getAMCObject(options.slot, options.shelf, options.debug)
printSystemSCAInfo(amcBoard, options.debug)
printSystemTTCInfo(amcBoard, options.debug)

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

THRESH_MIN = 0
THRESH_MAX = 254

N_EVENTS = gemData.Nev[0]
CHAN_MIN = 0
CHAN_MAX = 128
if options.debug:
    CHAN_MAX = 5
    pass

mask = options.vfatmask

try:
    writeAllVFATs(ohboard, options.gtx, "Latency",     0, mask)
    gemData.latency[0] = 0
    
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "VThreshold2", options.vt2, mask)

    # Get mspl value
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    0x0)
    msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),
                         range(0,24)))

    trgSrc = getTriggerSource(ohboard,options.gtx)
    if options.perchannel:
        setTriggerSource(ohboard,options.gtx,0x1)
        gemData.mode[0] = scanmode.THRESHCH
        sendL1A(ohboard, options.gtx, interval=250, number=0)

        for scCH in range(CHAN_MIN,CHAN_MAX):
            gemData.vfatCH[0] = scCH
            print "Channel #"+str(scCH)
            configureScanModule(ohboard, options.gtx, gemData.mode[0], mask, channel=scCH,
                                scanmin=THRESH_MIN, scanmax=THRESH_MAX,
                                numtrigs=int(N_EVENTS),
                                useUltra=True, debug=options.debug)
            printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)

            startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
            scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
            sys.stdout.flush()
            for i in range(0,24):
            	if (mask >> i) & 0x1: continue
                dataNow      = scanData[i]
                gemData.vfatN[0] = i
                gemData.mspl[0]  = msplvals[gemData.vfatN[0]]
                gemData.trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
                for VC in range(THRESH_MAX-THRESH_MIN+1):
                    gemData.vth1[0]  = int((dataNow[VC] & 0xff000000) >> 24)
                    gemData.vth[0]   = gemData.vth2[0] - gemData.vth1[0]
                    gemData.Nhits[0] = int(dataNow[VC] & 0xffffff)
                    gemData.gemTree.Fill()
                    pass
                pass
            gemData.gemTree.AutoSave("SaveSelf")
            pass

        setTriggerSource(ohboard,options.gtx,trgSrc)
        stopLocalT1(ohboard, options.gtx)
        pass
    else:
        if options.trkdata:
            setTriggerSource(ohboard,options.gtx,0x1)
            gemData.mode[0] = scanmode.THRESHTRK
            sendL1A(ohboard, options.gtx, interval=250, number=0)
        else:
            gemData.mode[0] = scanmode.THRESHTRG
            pass
        configureScanModule(ohboard, options.gtx, gemData.mode[0], mask,
                            scanmin=THRESH_MIN, scanmax=THRESH_MAX,
                            numtrigs=int(N_EVENTS),
                            useUltra=True, debug=options.debug)
        printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)

        startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
        scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
        sys.stdout.flush()
        for i in range(0,24):
            if (mask >> i) & 0x1: continue
            dataNow      = scanData[i]
            gemData.vfatN[0] = i
            gemData.trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
            for VC in range(THRESH_MAX-THRESH_MIN+1):
                gemData.vth1[0]  = int((dataNow[VC] & 0xff000000) >> 24)
                gemData.vth[0]   = gemData.vth2[0] - gemData.vth1[0]
                gemData.Nhits[0] = int(dataNow[VC] & 0xffffff)
                gemData.gemTree.Fill()
                pass
            pass
        gemData.gemTree.AutoSave("SaveSelf")

        if options.trkdata:
            setTriggerSource(ohboard,options.gtx,trgSrc)
            stopLocalT1(ohboard, options.gtx)
            pass
        pass

    # Place VFATs back in sleep mode
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)

except Exception as e:
    gemData.gemTree.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.gemTree.Write()
    myF.Close()
