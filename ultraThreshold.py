#!/bin/env python
"""
Script to take VT1 data using OH ultra scans
By: Cameron Bravo c.bravo@cern.ch
"""

import sys, os, random, time
from array import array

from gempython.tools.optohybrid_user_functions_uhal import *
from gempython.tools.vfat_functions_uhal import *

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
    uhal.setLogLevelTo( uhal.LogLevel.DEBUG )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('thrTree','Tree Holding CMS GEM VT1 Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = 1000
myT.Branch( 'Nev', Nev, 'Nev/I' )
vth = array( 'i', [ 0 ] )
myT.Branch( 'vth', vth, 'vth/I' )
vth1 = array( 'i', [ 0 ] )
myT.Branch( 'vth1', vth, 'vth1/I' )
vth2 = array( 'i', [ 0 ] )
myT.Branch( 'vth2', vth, 'vth2/I' )
vth2[0] = options.vt2
Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

THRESH_MIN = 0
THRESH_MAX = 100

N_EVENTS = Nev[0]
CHAN_MIN = 0
CHAN_MAX = 128
if options.debug:
    CHAN_MAX = 5
    pass
mask = 0

try:
    writeAllVFATs(ohboard, options.gtx, "Latency",     0, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "VThreshold2", options.vt2, mask)

    if options.perchannel or options.trkdata:
        mode = scanmode.THRESHTRK
        if options.perchannel:
            scanmode.THRESHCH
            pass
        sendL1A(ohboard, options.gtx, interval=250, number=0)

        for scCH in range(CHAN_MIN,CHAN_MAX):
            vfatCH[0] = scCH
            print "Channel #"+str(scCH)
            configureScanModule(ohboard, options.gtx, mode, mask, channel = scCH,
                                scanmin = THRESH_MIN, scanmax = THRESH_MAX,
                                numtrigs = int(N_EVENTS),
                                useUltra = True, debug = options.debug)
            printScanConfiguration(ohboard, options.gtx, useUltra = True, debug = options.debug)
            startScanModule(ohboard, options.gtx, useUltra = True, debug = options.debug)
            scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
            sys.stdout.flush()
            for i in range(0,24):
                vfatN[0] = i
                dataNow = scanData[i]
                for VC in range(THRESH_MAX-THRESH_MIN+1):
                    vth1[0] = int((dataNow[VC] & 0xff000000) >> 24)
                    vth[0]  = vth2[0] - vth1[0]
                    Nhits[0] = int(dataNow[VC] & 0xffffff)
                    myT.Fill()
                    pass
                pass
            myT.AutoSave("SaveSelf")
            pass

        stopLocalT1(ohboard, options.gtx)
        pass
    else:
        configureScanModule(ohboard, options.gtx, scanmode.THRESHTRG, mask,
                            scanmin = THRESH_MIN, scanmax = THRESH_MAX,
                            numtrigs = int(N_EVENTS),
                            useUltra = True, debug = options.debug)
        printScanConfiguration(ohboard, options.gtx, useUltra = True, debug = options.debug)
        startScanModule(ohboard, options.gtx, useUltra = True, debug = options.debug)
        scanData = getUltraScanResults(ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)
        sys.stdout.flush()
        for i in range(0,24):
            vfatN[0] = i
            dataNow = scanData[i]
            for VC in range(THRESH_MAX-THRESH_MIN+1):
                vth1[0] = int((dataNow[VC] & 0xff000000) >> 24)
                vth[0]  = vth2[0] - vth1[0]
                Nhits[0] = int(dataNow[VC] & 0xffffff)
                myT.Fill()
                pass
            pass
        myT.AutoSave("SaveSelf")
        pass
except Exception as e:
    myT.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    myT.Write()
    myF.Close()
