#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_uhal import *

from gempython.vfatqc.qcoptions import parser

parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--latency", type="int", dest = "latency", default = 37,
                  help="Specify Latency", metavar="latency")
parser.add_option("--CalPhase", type="int", dest = "CalPhase", default = 0,
                  help="Specify CalPhase. Must be in range 0-8", metavar="CalPhase")
parser.add_option("--L1Atime", type="int", dest = "L1Atime", default = 250,
                  help="Specify time between L1As in bx", metavar="L1Atime")
parser.add_option("--pulseDelay", type="int", dest = "pDel", default = 40,
                  help="Specify time of pulse before L1A in bx", metavar="pDel")
parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                  help="Specify minimum channel number to scan", metavar="chMin")
parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                  help="Specify maximum channel number to scan", metavar="chMax")

(options, args) = parser.parse_args()

if options.MSPL < 1 or options.MSPL > 8:
    print 'MSPL must be in the range 1-8'
    exit(1)
    pass
if options.CalPhase < 0 or options.CalPhase > 8:
    print 'CalPhase must be in the range 0-8'
    exit(1)
    pass
if not (0 <= options.chMin <= options.chMax < 128):
    print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
    exit(1)
    pass

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.INFO )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')

import subprocess,datetime,time
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

# Setup the output TTree
from gempython.vfatqc.treeStructure import gemTreeStructure
gemData = gemTreeStructure('scurveTree','Tree Holding CMS GEM SCurve Data',scanmode.SCURVE)
gemData.setDefaults(options, int(time.time()))

from gempython.tools.amc_user_functions_uhal import *
amcBoard = getAMCObject(options.slot, options.shelf, options.debug)
printSystemSCAInfo(amcBoard, options.debug)
printSystemTTCInfo(amcBoard, options.debug)

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

SCURVE_MIN = 0
SCURVE_MAX = 254

N_EVENTS = options.nevts
CHAN_MIN = options.chMin
CHAN_MAX = options.chMax + 1
if options.debug:
    CHAN_MAX = 5
    pass

mask = options.vfatmask

try:
    setTriggerSource(ohboard,options.gtx,1)
    configureLocalT1(ohboard, options.gtx, 1, 0, options.pDel, options.L1Atime, 0, options.debug)
    startLocalT1(ohboard, options.gtx)

    l1AInterval = readRegister(ohboard,"GEM_AMC.OH.OH%d.T1Controller.INTERVAL"%(options.gtx),options.debug)
    pulseDelay = readRegister(ohboard,"GEM_AMC.OH.OH%d.T1Controller.DELAY"%(options.gtx),options.debug)

    print 'Link %i T1 controller status: %i'%(options.gtx,getLocalT1Status(ohboard,options.gtx))

    writeAllVFATs(ohboard, options.gtx, "Latency",    options.latency, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",   (options.MSPL - 1) << 4, mask)
    writeAllVFATs(ohboard, options.gtx, "CalPhase",  0xff >> (8 - options.CalPhase), mask)

    vals = readAllVFATs(ohboard, options.gtx, "CalPhase",   0x0)
    calPhasevals = dict(map(lambda slotID: (slotID, bin(vals[slotID]).count("1")),
                         range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    0x0)
    msplvals =  dict(map(lambda slotID: (slotID, (1+(vals[slotID]>>4)&0x7)),
                         range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg3",    0x0)
    trimRangevals = dict(map(lambda slotID: (slotID, (0x07 & vals[slotID])),
                         range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "Latency",    0x0)
    latvals = dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                         range(0,24)))
    vfatIDvals = getAllChipIDs(ohboard, options.gtx, 0x0)
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold1", 0x0)
    vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold2", 0x0)
    vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                        range(0,24)))

    # Make sure no channels are receiving a cal pulse
    for vfat in range(0,24):
        if (mask >> vfat) & 0x1: continue
        for scCH in range(CHAN_MIN,CHAN_MAX):
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)

    for scCH in range(CHAN_MIN,CHAN_MAX):
        print "Channel #"+str(scCH)

        # Turn on the calpulse for channel scCH
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal+64)
        
        # Get trimDAC vals for output TTree
        vals = readAllVFATs(ohboard, options.gtx, "VFATChannels.ChanReg%d"%(scCH),   0x0)
        trimDACvals = dict(map(lambda slotID: (slotID, 0x1f & vals[slotID]),
                             range(0,24)))

        configureScanModule(ohboard, options.gtx, gemData.getMode(), mask, channel = scCH,
                            scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS),
                            useUltra = True, debug = options.debug)
        printScanConfiguration(ohboard, options.gtx, useUltra = True, debug = options.debug)
        startScanModule(ohboard, options.gtx, useUltra = True, debug = options.debug)
        scanData = getUltraScanResults(ohboard, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            dataNow = scanData[vfat]
            for VC in range(SCURVE_MAX-SCURVE_MIN+1):
                try:
                    vcal  = int((dataNow[VC] & 0xff000000) >> 24)
                    Nhits = int(dataNow[VC] & 0xffffff)
                except IndexError:
                    print 'Unable to index data for channel %i'%scCH
                    print dataNow
                    vcal  = -99
                    Nhits = -99
                finally:
                    gemData.fill(
                           calPhase = calPhasevals[vfat],
                           l1aTime = l1AInterval,
                           latency = latvals[vfat],
                           mspl = msplvals[vfat],
                           Nhits = Nhits, 
                           pDel = pulseDelay,
                           trimDAC = trimDACvals[vfat],
                           trimRange = trimRangevals[vfat],
                           vcal = vcal,
                           vfatCH = scCH,
                           vfatID = vfatIDvals[vfat],
                           vfatN = vfat,
                           vth = vthvals[vfat],
                           vth1 = vt1vals[vfat],
                           vth2 = vt2vals[vfat]
                         )

        # Turn off the calpulse for channel scCH
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)
        
        gemData.autoSave()
        sys.stdout.flush()
        pass
    stopLocalT1(ohboard, options.gtx)
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)

except Exception as e:
    gemData.autoSave()
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.write()
    myF.Close()
