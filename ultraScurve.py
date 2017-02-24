#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
"""

#import sys, os, random, time
from array import array
from GEMDAQTestSuite import *
from vfat_functions_uhal import *
from optparse import OptionParser
from ROOT import TFile,TTree

parser = OptionParser()

parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot", default=10)
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the GLIB", metavar="gtx", default=0)
parser.add_option("--nglib", type="int", dest="nglib",
                  help="Number of register tests to perform on the glib (default is 100)", metavar="nglib", default=100)
parser.add_option("--noh", type="int", dest="noh",
                  help="Number of register tests to perform on the OptoHybrid (default is 100)", metavar="noh", default=100)
parser.add_option("--ni2c", type="int", dest="ni2c",
                  help="Number of I2C tests to perform on the VFAT2s (default is 100)", metavar="ni2c", default=100)
parser.add_option("--ntrk", type="int", dest="ntrk",
                  help="Number of tracking data packets to readout (default is 100)", metavar="ntrk", default=100)
parser.add_option("--writeout", action="store_true", dest="writeout",
                  help="Write the data to disk when testing the rate", metavar="writeout")
parser.add_option("--tests", type="string", dest="tests",default="A,B,C,D,E",
                  help="Tests to run, default is all", metavar="tests")
parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

(options, args) = parser.parse_args()

filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('scurveTree','Tree Holding CMS GEM SCurve Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = 1000
myT.Branch( 'Nev', Nev, 'Nev/I' )
vcal = array( 'i', [ 0 ] )
myT.Branch( 'vcal', vcal, 'vcal/I' )
Nhits = array( 'i', [ 0 ] )
myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
trimRange = array( 'i', [ 0 ] )
myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
vthr = array( 'i', [ 0 ] )
myT.Branch( 'vthr', vthr, 'vthr/I' )
trimDAC = array( 'i', [ 0 ] )
myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

test_params = TEST_PARAMS(nglib=options.nglib,
                          noh=options.noh,
                          ni2c=options.ni2c,
                          ntrk=options.ntrk,
                          writeout=options.writeout)

testSuite = GEMDAQTestSuite(slot=options.slot,
                            gtx=options.gtx,
                            tests=options.tests,
                            test_params=test_params,
                            debug=options.debug)

testSuite.runSelectedTests()
testSuite.report()

SCURVE_MIN = 0
SCURVE_MAX = 254

N_EVENTS = Nev[0]
CHAN_MIN = 0
CHAN_MAX = 128
mask = 0

setTriggerSource(testSuite.glib,options.gtx,1)
configureLocalT1(testSuite.glib, options.gtx, 1, 0, 40, 250, 0, options.debug)
startLocalT1(testSuite.glib, options.gtx)


writeAllVFATs(testSuite.glib, options.gtx, "Latency",    37, mask)
writeAllVFATs(testSuite.glib, options.gtx, "ContReg0",    0x37, mask)
writeAllVFATs(testSuite.glib, options.gtx, "ContReg2",    48, mask)

for vfat in testSuite.presentVFAT2sSingle:
    for scCH in range(CHAN_MIN,CHAN_MAX):
        trimVal = (0x3f & readVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1)))
        writeVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1),trimVal)

for scCH in range(CHAN_MIN,CHAN_MAX):
    vfatCH[0] = scCH
    print "Channel #"+str(scCH)
    for vfat in testSuite.presentVFAT2sSingle:
        trimVal = (0x3f & readVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1)))
        writeVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1),trimVal+64)
    configureScanModule(testSuite.glib, options.gtx, 3, mask, channel = scCH, scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS), useUltra = True, debug = options.debug)
    printScanConfiguration(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
    startScanModule(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
    scanData = getUltraScanResults(testSuite.glib, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)
    for i in range(0,24):
        vfatN[0] = i
        dataNow = scanData[i]
        trimRange[0] = (0x7 & readVFAT(testSuite.glib,options.gtx, i,"ContReg3"))
        trimDAC[0] = (0x1f & readVFAT(testSuite.glib,options.gtx, i,"VFATChannels.ChanReg%d"%(scCH+1)))
        vthr[0] = (0xff & readVFAT(testSuite.glib,options.gtx, i,"VThreshold1"))
        for VC in range(SCURVE_MIN,SCURVE_MAX+1):
            vcal[0] = int((dataNow[VC] & 0xff000000) >> 24)
            Nhits[0] = int(dataNow[VC] & 0xffffff)
            myT.Fill()
    for vfat in testSuite.presentVFAT2sSingle:
        trimVal = (0x3f & readVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1)))
        writeVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1),trimVal)

stopLocalT1(testSuite.glib, options.gtx)
writeAllVFATs(testSuite.glib, options.gtx, "ContReg0",    0, mask)

myF.cd()
myT.Write()
myF.Close()






