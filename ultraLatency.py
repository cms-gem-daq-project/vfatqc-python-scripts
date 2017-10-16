#!/bin/env python
"""
Script to take latency data using OH ultra scans
By: Jared Sturdy  (sturdy@cern.ch)
    Cameron Bravo (c.bravo@cern.ch)
    Brian Dorney (brian.l.dorney@cern.ch)
"""

import sys, os, random, time
from array import array
from ctypes import *

from gempython.tools.vfat_user_functions_xhal import *

from gempython.vfatqc.qcoptions import parser

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
parser.add_option("--t3trig", action="store_true", dest="t3trig",
                  help="Set up for using AMC13 T3 trigger input", metavar="t3trig")
parser.add_option("--throttle", type="int", default=0, dest="throttle",
                  help="factor by which to throttle the input L1A rate, e.g. new trig rate = L1A rate / throttle", metavar="throttle")
parser.add_option("--vt2", type="int", dest="vt2",
                  help="VThreshold2 DAC value for all VFATs (v2b electronics only)", metavar="vt2", default=0)

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

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('latTree','Tree Holding CMS GEM Latency Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = -1
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
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print(startTime)
Date = startTime

# Setup the output TTree
from treeStructure import gemTreeStructure
gemData = gemTreeStructure('latTree','Tree Holding CMS GEM Latency Data',scanmode.LATENCY)
gemData.setDefaults(options, int(time.time()))

import amc13
connection_file = "%s/connections.xml"%(os.getenv("GEM_ADDRESS_TABLE_PATH"))
amc13base  = "gem.shelf%02d.amc13"%(options.shelf)
amc13board = amc13.AMC13(connection_file,"%s.T1"%(amc13base),"%s.T2"%(amc13base))

vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)

mask = options.vfatmask

try:
    vfatBoard.setRunModeAll(mask, True, options.debug)
    vfatBoard.setVFATMSPLAll(mask, options.MSPL, options.debug)
    
    if vfatBoard.parentOH.parentAMC.fwVersion > 2:
        vals  = vfatBoard.readAllVFATs("CFG_THR_ARM_DAC", mask)
        vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                            range(0,24)))
        vals = vfatBoard.readAllVFATs("CFG_PULSE_STRETCH", mask)
        msplvals =  dict(map(lambda slotID: (slotID, vals[slotID]),
                             range(0,24)))
    else:
        vfatBoard.writeAllVFATs("VThreshold2", options.vt2, mask)

        vals  = vfatBoard.readAllVFATs("VThreshold1", 0x0)
        vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                            range(0,24)))
        vals  = vfatBoard.readAllVFATs("VThreshold2", 0x0)
        vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                            range(0,24)))
        vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                            range(0,24)))
        vals = vfatBoard.readAllVFATs("ContReg2",    0x0)
        msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),
                             range(0,24)))

    #mode = scanmode.LATENCY

    #oh.stopLocalT1(ohboard, options.gtx)

    #amc13board.enableLocalL1A(False)
    #amc13board.resetCounters()

    #scanBase = "GEM_AMC.OH.OH%d.ScanController.ULTRA"%(options.gtx)
    #if (readRegister(ohboard,"%s.MONITOR.STATUS"%(scanBase)) > 0):
    #    print("Scan was already running, resetting module")
    #    writeRegister(ohboard,"%s.RESET"%(scanBase),0x1)
    #    time.sleep(0.1)
    #    pass
    amc13nL1A = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
    #amcnL1A = amc.getL1ACount(amcboard)
    #ohnL1A = oh.getL1ACount(ohboard,options.gtx)
    #print "Initial L1A counts:"
    print "AMC13: %s"%(amc13nL1A)
    #print "AMC: %s"%(amcnL1A)
    #print "OH%s: %s"%(options.gtx,ohnL1A)
    #oh.configureScanModule(ohboard, options.gtx, mode, mask,
    #                    scanmin=LATENCY_MIN, scanmax=LATENCY_MAX,
    #                    stepsize=step,
    #                    numtrigs=int(options.nevts),
    #                    useUltra=True, debug=True)
    #oh.printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    #sys.stdout.flush()
    #amc13board.enableLocalL1A(True)

    if options.internal:
        #amc.blockL1A(amcboard)
        #oh.setTriggerSource(ohboard,options.gtx,0x1)
        #oh.sendL1ACalPulse(ohboard, options.gtx, delay=20, interval=400, number=0)
        #chanReg = ((1&0x1) << 6)|((0&0x1) << 5)|(0&0x1f)
        #writeAllVFATs(ohboard, options.gtx, "VFATChannels.ChanReg0", chanReg, mask)
        #writeAllVFATs(ohboard, options.gtx, "VCal",     250, mask)

        # Configure TTC
        if 0 == vfatBoard.parentOH.parentAMC.ttcGenConf(options.L1Atime, options.pDel):
            print "TTC configured successfully"
        else:
            print "TTC configuration failed"
            sys.exit(os.EX_CONFIG)
    else:
        if options.amc13local:
            #amc.enableL1A(amcboard)
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
                amc13board.configureLocalL1A(True, 0, 1, 1, 0) # per-orbit
                pass
            if options.t3trig:
                amc13board.write(amc13board.Board.T1, 'CONF.TTC.T3_TRIG', 0x1)
                pass
            # to prevent trigger blocking
            amc13board.fakeDataEnable(True)
            amc13board.enableLocalL1A(True)
            if options.randoms > 0:
                amc13board.startContinuousL1A()
                pass
            pass
        #amc.enableL1A(amcboard)
        #oh.setTriggerSource(ohboard,options.gtx,0x5) # GBT, 0x0 for GTX
        pass

    #oh.setTriggerThrottle(ohboard, options.gtx, options.throttle)
    #oh.startScanModule(ohboard, options.gtx, useUltra=True, debug=options.debug)
    #oh.printScanConfiguration(ohboard, options.gtx, useUltra=True, debug=options.debug)
    sys.stdout.flush()
    #scanData = oh.getUltraScanResults(ohboard, options.gtx, LATENCY_MAX - LATENCY_MIN + 1, options.debug)
    chan = 69
    scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
    scanDataSizeNet = scanDataSizeVFAT * 24
    scanData = (c_uint32 * scanDataSizeNet)()
    rpcResp = vfatBoard.parentOH.genScan(options.nevts, options.gtx,
                                         options.scanmin,options.scanmax,options.stepSize,
                                         chan,1,options.vfatmask,"LATENCY",scanData)

    if rpcResp != 0:
        print("latency scan for channel %i failed"%chan)
        sys.exit(os.EX_SOFTWARE)

    print("Done scanning, processing output")
    amc13board.enableLocalL1A(False)
    amc13nL1Af = (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_HI") << 32) | (amc13board.read(amc13board.Board.T1, "STATUS.GENERAL.L1A_COUNT_LO"))
    #amcnL1Af = amc.getL1ACount(amcboard)
    #ohnL1Af = oh.getL1ACount(ohboard,options.gtx)
    print "Final L1A counts:"
    print "AMC13: %s, difference %s"%(amc13nL1Af,amc13nL1Af-amc13nL1A)
    #print "AMC: %s, difference %s"%(amcnL1Af,amcnL1Af-amcnL1A)
    #print "OH%s: %s, difference %s"%(options.gtx,ohnL1Af,ohnL1Af-ohnL1A)

    #for i in range(24):
    #  print "Total number of CRC packets for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)) + readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.VALID.VFAT%d"%(options.gtx,i)))
    #for i in range(24):
    #  print "Number of CRC errors for VFAT%s on link %s is %s"%(i, options.gtx, readRegister(ohboard,"GEM_AMC.OH.OH%d.COUNTERS.CRC.INCORRECT.VFAT%d"%(options.gtx,i)))

    amc13board.enableLocalL1A(True)
    sys.stdout.flush()
    for vfat in range(0,24):
        vfatN[0] = vfat
        #dataNow = scanData[i]
        mspl[0]  = msplvals[vfatN[0]]
        vth1[0]  = vt1vals[vfatN[0]]
        #vth2[0]  = vt2vals[vfatN[0]]
        #vth[0]   = vthvals[vfatN[0]]
        if options.debug:
            #print("{0} {1} {2} {3} {4}".format(vfatN[0], mspl[0], vth1[0], vth2[0], vth[0]))
            sys.stdout.flush()
            pass
        for latReg in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT,options.stepSize):
            #lat[0]   = int((dataNow[VC] & 0xff000000) >> 24)
            #Nhits[0] = int(dataNow[VC] & 0xffffff)
            #if options.debug:
            #    print("{0} {1} 0x{2:x} {3} {4}".format(i,VC,dataNow[VC],lat[0],Nhits[0]))
            #    pass
            try:
                if vfat == 0:
                    lat[0] = latReg
                else:
                    lat[0] = latReg - vfat*scanDataSizeVFAT
                Nev[0] = scanData[latReg] & 0xffff
                Nhits[0] = (scanData[latReg]>>16) & 0xffff
                #print vfat,chan,latReg,lat[0],Nhits[0],Nev[0]
            except IndexError:
                print 'Unable to index data for channel %i'%chan
                print scanData[latReg]
                vth1[0]  = -99
                Nhits[0] = -99
            finally:
                myT.Fill()
            pass
        pass
    myT.AutoSave("SaveSelf")
    vfatBoard.setRunModeAll(mask, False, options.debug)
    if options.internal:
        #oh.stopLocalT1(ohboard, options.gtx)
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
