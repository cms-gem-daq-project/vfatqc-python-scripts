#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch) and Brian Dorney (brian.l.dorney@cern.ch)
"""

from array import array
from ctypes import *
#from gempython.tools.vfat_user_functions_uhal import *

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

(options, args) = parser.parse_args()

#if options.MSPL < 1 or options.MSPL > 8:
#    print 'MSPL must be in the range 1-8'
#    exit(1)
#    pass
#if options.CalPhase < 0 or options.CalPhase > 8:
#    print 'CalPhase must be in the range 0-8'
#    exit(1)
#    pass
if not (0 <= options.chMin <= options.chMax < 128):
    print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
    exit(1)
    pass

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

from rpcService import *
from gempython.gemplotting.mapping.amcInfo import ctp7Params 
rpc_connect(ctp7Params.cardLocation[(options.shelf, options.slot)])
print 'opened connection'
#ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

#SCURVE_MIN = 0
#SCURVE_MAX = 254

# N_EVENTS = options.nevts
CHAN_MIN = options.chMin
CHAN_MAX = options.chMax + 1
if options.debug:
    CHAN_MAX = 5
    pass

mask = options.vfatmask

try:
    #setTriggerSource(ohboard,options.gtx,1)
    #configureLocalT1(ohboard, options.gtx, 1, 0, options.pDel, options.L1Atime, 0, options.debug)
    #startLocalT1(ohboard, options.gtx)

    #print 'Link %i T1 controller status: %i'%(options.gtx,getLocalT1Status(ohboard,options.gtx))

    # Test
    #configureVFAT3s(options.gtx, options.vfatmask)

    # Configure TTC
    if 0 == ttcGenConf(options.L1Atime, options.pDel):
        print "TTC configured successfully"
    else:
        print "TTC configuration failed"
        sys.exit(os.EX_CONFIG)

    #writeAllVFATs(ohboard, options.gtx, "Latency",    options.latency, mask)
    #writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x37, mask)
    #writeAllVFATs(ohboard, options.gtx, "ContReg2",   (options.MSPL - 1) << 4, mask)
    #writeAllVFATs(ohboard, options.gtx, "CalPhase",  0xff >> (8 - options.CalPhase), mask)

    #for vfat in range(0,24):
    #    if (mask >> vfat) & 0x1: continue
    #    for scCH in range(CHAN_MIN,CHAN_MAX):
    #        trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
    #        writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)

    scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
    scanDataSizeNet = scanDataSizeVFAT * 24
    scanData = (c_uint32 * scanDataSizeNet)()
    for chan in range(CHAN_MIN,CHAN_MAX):
        vfatCH[0] = chan
        print "Channel #"+str(chan)
        #for vfat in range(0,24):
        #    if (mask >> vfat) & 0x1: continue
        #    trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
        #    writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal+64)
        #configureScanModule(ohboard, options.gtx, scanmode.SCURVE, mask, channel = scCH,
        #                    scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS),
        #                    useUltra = True, debug = options.debug)
        #printScanConfiguration(ohboard, options.gtx, useUltra = True, debug = options.debug)
        #startScanModule(ohboard, options.gtx, useUltra = True, debug = options.debug)
        #scanData = getUltraScanResults(ohboard, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)
        rpcResp = genScan(  options.nevts, options.gtx,
                            options.scanmin,options.scanmax,options.stepSize,
                            chan,1,options.vfatmask,"CAL_DAC",scanData)

        if rpcResp != 0:
            print("scurve for channel %i failed"%chan)
            sys.exit(os.EX_SOFTWARE)
        #else:
        #    print scanData
        #    print len(scanData)

        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            vfatN[0] = vfat
            #dataNow = scanData[vfat]
            #trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
            #trimDAC[0]   = (0x1f & readVFAT(ohboard,options.gtx, i,"VFATChannels.ChanReg%d"%(scCH)))
            #vthr[0]      = (0xff & readVFAT(ohboard,options.gtx, i,"VThreshold1"))
            for vcalDAC in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT,options.stepSize):
                try:
                    #vcal[0]  = int((dataNow[VC] & 0xff000000) >> 24)
                    #Nhits[0] = int(dataNow[VC] & 0xffffff)
                    if vfat == 0:
                        #vcal[0] = vcalDAC
                        vcal[0] = scanDataSizeVFAT - vcalDAC
                    else:
                        #vcal[0] = vcalDAC - vfat*scanDataSizeVFAT
                        vcal[0] = (vfat+1)*scanDataSizeVFAT - vcalDAC
                    Nev[0] = scanData[vcalDAC] & 0xffff
                    Nhits[0] = (scanData[vcalDAC]>>16) & 0xffff
                    #Nhits[0] = scanData[vcalDAC]
                    print vfat,chan,vcalDAC,vcal[0],Nhits[0],Nev[0]
                except IndexError:
                    print 'Unable to index data for channel %i'%chan
                    print scanData[vcalDAC]
                    vcal[0]  = -99
                    Nhits[0] = -99
                finally:
                    myT.Fill()
        #for vfat in range(0,24):
        #    if (mask >> vfat) & 0x1: continue
        #    trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
        #    writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)
        #myT.AutoSave("SaveSelf")
        #sys.stdout.flush()
        #pass
    #stopLocalT1(ohboard, options.gtx)
    #writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)

except Exception as e:
    gemData.autoSave()
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.write()
    myF.Close()
