#!/bin/env python
"""
Script to take latency data using OH ultra scans
By: Jared Sturdy  (sturdy@cern.ch)
    Cameron Bravo (c.bravo@cern.ch)
Modified By:
    Brian Dorney (brian.l.dorney@cern.ch)
"""

import sys, os, random, time
from array import array

import gempython.tools.optohybrid_user_functions_uhal as oh
from gempython.tools.vfat_user_functions_uhal import *
import gempython.tools.amc_user_functions_uhal as amc

from qcoptions import parser

parser.add_option("--amc13local", action="store_true", dest="amc13local",
                  help="Set up for using AMC13 local trigger generator", metavar="amc13local")
parser.add_option("--fakeTTC", action="store_true", dest="fakeTTC",
                  help="Set up for using AMC13 local TTC generator", metavar="fakeTTC")
parser.add_option("--filename", type="string", dest="filename", default="LatencyData_Trimmed.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--internal", action="store_true", dest="internal",
                  help="Run a latency scan using the internal calibration pulse", metavar="internal")
parser.add_option("--randoms", type="int", default=0, dest="randoms",
                  help="Set up for using AMC13 local trigger generator to generate random triggers with rate specified",
                  metavar="randoms")
parser.add_option("--stepSize", type="int", dest="stepSize", 
                  help="Supply a step size to the latency scan from scanmin to scanmax", metavar="stepSize", default=1)
parser.add_option("--t3trig", action="store_true", dest="t3trig",
                  help="Set up for using AMC13 T3 trigger input", metavar="t3trig")
parser.add_option("--throttle", type="int", default=0, dest="throttle",
                  help="factor by which to throttle the input L1A rate, e.g. new trig rate = L1A rate / throttle", metavar="throttle")
parser.add_option("--vt2", type="int", dest="vt2", default=0,
                  help="Specify VT2 to use", metavar="vt2")

parser.set_defaults(scanmin=153,scanmax=172,nevts=500)
(options, args) = parser.parse_args()

if options.scanmin not in range(256) or options.scanmax not in range(256) or not (options.scanmax > options.scanmin):
    print("Invalid scan parameters specified [min,max] = [%d,%d]"%(options.scanmin,options.scanmax))
    print("Scan parameters must be in range [0,255] and min < max")
    exit(1)

if options.vt2 not in range(256):
    print("Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2))
    exit(1)

if options.MSPL not in range(1,9):
    print("Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL))
    exit(1)

if options.stepSize <= 0:
    print("Invalid stepSize specified: %d, must be in range [1, %d]"%(options.stepSize, options.scanmax-options.scanmin))
    exit(1)

step = options.stepSize
if (step + options.scanmin > options.scanmax):
    step = options.scanmax - options.scanmin

if options.debug:
    uhal.setLogLevelTo(uhal.LogLevel.INFO)
else:
    uhal.setLogLevelTo(uhal.LogLevel.ERROR)

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')

# Setup the output TTree
from treeStructure import gemTreeStructure
gemData = gemTreeStructure('latTree','Tree Holding CMS GEM Latency Data',scanmode.LATENCY)
gemData.setDefaults(options)

import subprocess,datetime,time
gemData.utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print(startTime)
Date = startTime

import amc13
connection_file = "%s/connections.xml"%(os.getenv("GEM_ADDRESS_TABLE_PATH"))
amc13base  = "gem.shelf%02d.amc13"%(options.shelf)
amc13board = amc13.AMC13(connection_file,"%s.T1"%(amc13base),"%s.T2"%(amc13base))

amcboard = amc.getAMCObject(options.slot,options.shelf,options.debug)
amc.printSystemSCAInfo(amcboard, options.debug)
amc.printSystemTTCInfo(amcboard, options.debug)

ohboard  = oh.getOHObject(options.slot,options.gtx,options.shelf,options.debug)

LATENCY_MIN = options.scanmin
LATENCY_MAX = options.scanmax

N_EVENTS = gemData.Nev[0]

mask = options.vfatmask

try:
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",    ((options.MSPL-1)<<4))
    writeAllVFATs(ohboard, options.gtx, "VThreshold2", options.vt2, mask)

    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold1", 0x0)
    vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold2", 0x0)
    vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                        range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    0x0)
    msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),
                         range(0,24)))

    oh.stopLocalT1(ohboard, options.gtx)

    amc13board.enableLocalL1A(False)
    amc13board.resetCounters()

    scanBase = "GEM_AMC.OH.OH%d.ScanController.ULTRA"%(options.gtx)
    if (readRegister(ohboard,"%s.MONITOR.STATUS"%(scanBase)) > 0):
        print("Scan was already running, resetting module")
        writeRegister(ohboard,"%s.RESET"%(scanBase),0x1)
        time.sleep(0.1)
        pass
    amc13nL1A = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
    amcnL1A = amc.getL1ACount(amcboard)
    ohnL1A = oh.getL1ACount(ohboard,options.gtx)
    print "Initial L1A counts:"
    print "AMC13: %s"%(amc13nL1A)
    print "AMC: %s"%(amcnL1A)
    print "OH%s: %s"%(options.gtx,ohnL1A)
    oh.configureScanModule(ohboard, options.gtx, gemData.getMode(), mask,
                        scanmin=LATENCY_MIN, scanmax=LATENCY_MAX,
                        stepsize=step,
                        numtrigs=int(options.nevts),
                        useUltra=True, debug=True)
    oh.printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    sys.stdout.flush()
    amc13board.enableLocalL1A(True)

    if options.internal:
        amc.blockL1A(amcboard)
        oh.setTriggerSource(ohboard,options.gtx,0x1)
        oh.sendL1ACalPulse(ohboard, options.gtx, delay=20, interval=400, number=0)
        chanReg = ((1&0x1) << 6)|((0&0x1) << 5)|(0&0x1f)
        writeAllVFATs(ohboard, options.gtx, "VFATChannels.ChanReg0", chanReg, mask)
        writeAllVFATs(ohboard, options.gtx, "VCal",     250, mask)
    else:
        if options.amc13local:
            amc.enableL1A(amcboard)
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
                # amc13board.configureLocalL1A(True, 2, 1, options.randoms, 0)
                # amc13board.configureLocalL1A(True, 1, 1, 1, 0) # per-BX
                amc13board.configureLocalL1A(True, 0, 1, 1, 0) # per-orbit
                pass
            if options.t3trig:
                amc13board.write(amc13board.Board.T1, 'CONF.TTC.T3_TRIG', 0x1)
                pass
            # to prevent trigger blocking
            amc13board.fakeDataEnable(True)
            # disable the event builder?
            # amc13board.write(amc13board.Board.T1, 'CONF.DIAG.DISABLE_EVB', 0x1)
            amc13board.enableLocalL1A(True)
            if options.randoms > 0:
                amc13board.startContinuousL1A()
                pass
            pass
        amc.enableL1A(amcboard)
        oh.setTriggerSource(ohboard,options.gtx,0x5) # GBT, 0x0 for GTX
        pass

    oh.setTriggerThrottle(ohboard, options.gtx, options.throttle)
    oh.startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
    oh.printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    sys.stdout.flush()
    scanData = oh.getUltraScanResults(ohboard, options.gtx, LATENCY_MAX - LATENCY_MIN + 1, options.debug)

    print("Done scanning, processing output")
    amc13board.enableLocalL1A(False)
    amc13nL1Af = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
    amcnL1Af = amc.getL1ACount(amcboard)
    ohnL1Af = oh.getL1ACount(ohboard,options.gtx)
    print "Final L1A counts:"
    print "AMC13: %s, difference %s"%(amc13nL1Af,amc13nL1Af-amc13nL1A)
    print "AMC: %s, difference %s"%(amcnL1Af,amcnL1Af-amcnL1A)
    print "OH%s: %s, difference %s"%(options.gtx,ohnL1Af,ohnL1Af-ohnL1A)

    for i in range(24):
      print "Total number of CRC packets for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)) + readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.VALID.VFAT%d"%(options.gtx,i)))
    for i in range(24):
      print "Number of CRC errors for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)))

    amc13board.enableLocalL1A(True)
    sys.stdout.flush()
    for i in range(0,24):
        dataNow = scanData[i]
        gemData.vfatN[0] = i
        gemData.mspl[0]  = msplvals[gemData.vfatN[0]]
        gemData.vth1[0]  = vt1vals[gemData.vfatN[0]]
        gemData.vth2[0]  = vt2vals[gemData.vfatN[0]]
        gemData.vth[0]   = vthvals[gemData.vfatN[0]]
        if options.debug:
            print("{0} {1} {2} {3} {4}".format(
                gemData.vfatN[0], 
                gemData.mspl[0], 
                gemData.vth1[0], 
                gemData.vth2[0], 
                gemData.vth[0]))
            sys.stdout.flush()
            pass
        for VC in range(LATENCY_MAX-LATENCY_MIN+1):
            latency   = int((dataNow[VC] & 0xff000000) >> 24)
            Nhits = int(dataNow[VC] & 0xffffff)
            gemData.setScanResults(latency, Nhits)
            if options.debug:
                print("{0} {1} 0x{2:x} {3} {4}".format(i,VC,dataNow[VC],gemData.latency[0],gemData.Nhits[0]))
                pass
            gemData.fill()
            pass
        pass
    gemData.autoSave()
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)
    if options.internal:
        oh.stopLocalT1(ohboard, options.gtx)
        pass
    elif options.amc13local:
        amc13board.stopContinuousL1A()
        amc13board.fakeDataEnable(False)
        # amc13board.write(amc13board.Board.T1, 'CONF.DIAG.DISABLE_EVB', 0x0)
        pass
except Exception as e:
    gemData.autoSave()
    print("An exception occurred", e)
finally:
    myF.cd()
    gemData.write()
    myF.Close()
