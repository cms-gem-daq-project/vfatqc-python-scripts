#!/bin/env python2.7
"""
Script to take latency data using OH ultra scans
By: Jared Sturdy  (sturdy@cern.ch)
    Cameron Bravo (c.bravo@cern.ch)
Modified By:
    Brian Dorney (brian.l.dorney@cern.ch)
"""

import sys, os, random, time
from array import array

from gempython.tools.optohybrid_user_functions_uhal import *
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)
parser.add_option("--vt2", type="int", dest="vt2", default=0,
                  help="Specify VT2 to use", metavar="vt2")
parser.add_option("--mspl", type="int", dest = "MSPL", default = 4,
                  help="Specify MSPL.  Must be in the range 1-8 (default is 4)", metavar="MSPL")
parser.add_option("--filename", type="string", dest="filename", default="LatencyData_Trimmed.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--internal", action="store_true", dest="internal",
                  help="Run a latency scan using the internal calibration pulse", metavar="internal")

parser.set_defaults(scanmin=153,scanmax=172,nevts=500)

(options, args) = parser.parse_args()

if options.scanmin not in range(256) or options.scanmax not in range(256) or not (options.scanmax > options.scanmin):
    print "Invalid scan parameters specified [min,max] = [%d,%d]"%(options.scanmin,options.scanmax)
    print "Scan parameters must be in range [0,255] and min < max"
    exit(1)

if options.vt2 not in range(256):
    print "Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2)
    exit(1)

if options.MSPL not in range(1,9):
    print "Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL)
    exit(1)

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.INFO )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('latTree','Tree Holding CMS GEM Latency Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = options.nevts
myT.Branch( 'Nev', Nev, 'Nev/I' )
vth = array( 'i', [ 0 ] )
myT.Branch( 'vth', vth, 'vth/I' )
vth1 = array( 'i', [ 0 ] )
myT.Branch( 'vth1', vth1, 'vth1/I' )
vth2 = array( 'i', [ 0 ] )
myT.Branch( 'vth2', vth2, 'vth2/I' )
lat = array( 'i', [ 0 ] )
myT.Branch( 'lat', lat, 'lat/I' )
Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
mspl = array( 'i', [ -1 ] )
myT.Branch( 'mspl', mspl, 'mspl/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx
utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import subprocess,datetime,time
utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

LATENCY_MIN = options.scanmin
LATENCY_MAX = options.scanmax

N_EVENTS = Nev[0]

mask = options.vfatmask

try:
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",    ((options.MSPL-1)<<4))
    writeAllVFATs(ohboard, options.gtx, "VThreshold2", options.vt2, mask)

    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold1", mask)
    vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold2", mask)
    vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                        range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    mask)
    msplvals =  dict(map(lambda slotID: (slotID, (vals[slotID]>>4)&0x7),
                         range(0,24)))

    mode = scanmode.LATENCY

    if options.internal:
        setTriggerSource(ohboard,options.gtx,0x1)
        # sendL1A(        ohboard, options.gtx, interval=250, number=0)
        sendL1ACalPulse(ohboard, options.gtx, delay=20, interval=400, number=0)
        chanReg = ((1&0x1) << 6)|((0&0x1) << 5)|(0&0x1f)
        writeAllVFATs(ohboard, options.gtx, "VFATChannels.ChanReg0", chanReg, mask)
        writeAllVFATs(ohboard, options.gtx, "VCal",     250, mask)
    else:
        # setTriggerSource(ohboard,options.gtx,0x0) # GTX
        setTriggerSource(ohboard,options.gtx,0x5) # GBT
        pass

    scanBase = "GEM_AMC.OH.OH%d.ScanController.ULTRA"%(options.gtx)
    if (readRegister(ohboard,"%s.MONITOR.STATUS"%(scanBase)) > 0):
        print "Scan was already running, resetting module"
        writeRegister(ohboard,"%s.RESET"%(scanBase),0x1)
        time.sleep(0.1)
        pass
    configureScanModule(ohboard, options.gtx, mode, mask,
                        scanmin=LATENCY_MIN, scanmax=LATENCY_MAX,
                        numtrigs=int(options.nevts),
                        useUltra=True, debug=True)
    printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    sys.stdout.flush()
    startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
    printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    sys.stdout.flush()
    scanData = getUltraScanResults(ohboard, options.gtx, LATENCY_MAX - LATENCY_MIN + 1, options.debug)

    for i in range(0,24):
        if (mask >> i) & 0x1: continue
        vfatN[0] = i
        dataNow = scanData[i]
        mspl[0]  = msplvals[vfatN[0]]
        vth1[0]  = vt1vals[vfatN[0]]
        vth2[0]  = vt2vals[vfatN[0]]
        vth[0]   = vthvals[vfatN[0]]
        if options.debug:
            print "{0} {1} {2} {3} {4}".format(vfatN[0], mspl[0], vth1[0], vth2[0], vth[0])
            sys.stdout.flush()
            pass
        for VC in range(LATENCY_MAX-LATENCY_MIN+1):
            lat[0]   = int((dataNow[VC] & 0xff000000) >> 24)
            Nhits[0] = int(dataNow[VC] & 0xffffff)
            if options.debug:
                print("{0} {1} 0x{2:x} {3} {4}".format(i,VC,dataNow[VC],lat[0],Nhits[0]))
                pass
            myT.Fill()
            pass
        pass
    myT.AutoSave("SaveSelf")
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)
    if options.internal:
        stopLocalT1(ohboard, options.gtx)
        pass
except Exception as e:
    myT.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    myT.Write()
    myF.Close()
