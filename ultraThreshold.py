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

parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData_Trimmed.root",
                  help="Specify Output Filename", metavar="filename")

(options, args) = parser.parse_args()

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
Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

THRESH_MIN = 0
THRESH_MAX = 100

N_EVENTS = Nev[0]
CHAN_MIN = 0
CHAN_MAX = 128
if options.debug:
    CHAN_MAX = 5
    pass
mask = 0

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

sendL1A(ohboard, options.gtx, interval=250, number=0)

writeAllVFATs(ohboard, options.gtx, "Latency",     0, mask)
writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x37, mask)

for scCH in range(CHAN_MIN,CHAN_MAX):
    vfatCH[0] = scCH
    print "Channel #"+str(scCH)
    configureScanModule(ohboard, options.gtx, 1, mask, channel = scCH,
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
        for VC in range(THRESH_MIN,THRESH_MAX+1):
            vth[0] = int((dataNow[VC] & 0xff000000) >> 24)
            Nhits[0] = int(dataNow[VC] & 0xffffff)
            myT.Fill()
            pass
        pass
    myT.AutoSave("SaveSelf")
    pass

stopLocalT1(ohboard, options.gtx)
myF.cd()
myT.Write()
myF.Close()

