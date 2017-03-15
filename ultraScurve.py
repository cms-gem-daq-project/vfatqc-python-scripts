#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
"""

#import sys, os, random, time
from array import array
import sys
from GEMDAQTestSuite import *
from vfat_functions_uhal import *
from optparse import OptionParser
from ROOT import TFile,TTree
from rw_reg import writeReg,rpc_connect,parseXML, getNode

parser = OptionParser()

parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot", default=10)
parser.add_option("--shelf", type="int", dest="shelf",
                  help="The uTCA crate", metavar="shelf", default=1)
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
parser.add_option("--tests", type="string", dest="tests",default="",
                  help="Tests to run, default is all", metavar="tests")
parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

(options, args) = parser.parse_args()
uhal.setLogLevelTo( uhal.LogLevel.WARNING )

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
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

connection_file = "file://${GEM_ADDRESS_TABLE_PATH}/connections.xml"
manager         = uhal.ConnectionManager(connection_file )
amc  = manager.getDevice( "gem.shelf%02d.amc%02d.optohybrid%02d"%(options.shelf,options.slot,options.gtx) )


SCURVE_MIN = 0
SCURVE_MAX = 254

N_EVENTS = Nev[0]
CHAN_MIN = 0
CHAN_MAX = 128
mask = 0

#bias vfats
#biasAllVFATs(testSuite.glib,options.gtx,0x0,enable=False)
#writeAllVFATs(testSuite.glib, options.gtx, "VThreshold1", 70, 0)

setTriggerSource(amc,options.gtx,1)
configureLocalT1(amc, options.gtx, 1, 0, 40, 250, 0, options.debug)
startLocalT1(amc, options.gtx)

print 'Link %i T1 controller status: %i'%(options.gtx,getLocalT1Status(amc,options.gtx))
writeAllVFATs(amc, options.gtx, "Latency",    37, mask)
writeAllVFATs(amc, options.gtx, "ContReg0",    0x37, mask)
writeAllVFATs(amc, options.gtx, "ContReg2",    48, mask)
print 'Configured Latency and MSPL'

for vfat in range(0,24):
    for scCH in range(CHAN_MIN,CHAN_MAX):
        trimVal = (0x3f & readVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
        writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)

for scCH in range(CHAN_MIN,CHAN_MAX):
    vfatCH[0] = scCH
    print "Channel #"+str(scCH)
    for vfat in range(0,24):
        trimVal = (0x3f & readVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
        writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal+64)
    configureScanModule(amc, options.gtx, 3, mask, channel = scCH, scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS), useUltra = True, debug = options.debug)
    printScanConfiguration(amc, options.gtx, useUltra = True, debug = options.debug)
    startScanModule(amc, options.gtx, useUltra = True, debug = options.debug)
    scanData = getUltraScanResults(amc, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)
    for i in range(0,24):
        vfatN[0] = i
        dataNow = scanData[i]
        trimRange[0] = (0x7 & readVFAT(amc,options.gtx, i,"ContReg3"))
        trimDAC[0] = (0x1f & readVFAT(amc,options.gtx, i,"VFATChannels.ChanReg%d"%(scCH)))
        vthr[0] = (0xff & readVFAT(amc,options.gtx, i,"VThreshold1"))
        for VC in range(SCURVE_MIN,SCURVE_MAX+1):
            try:
                vcal[0] = int((dataNow[VC] & 0xff000000) >> 24)
                Nhits[0] = int(dataNow[VC] & 0xffffff)
                myT.Fill()
            except IndexError:
                print 'Unable to index data for channel %i'%scCH
                print dataNow
                vcal[0] = -99
                Nhits[0] = -99
                myT.Fill()
    for vfat in range(0,24):
        trimVal = (0x3f & readVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
        writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)
    myT.AutoSave("SaveSelf")
    sys.stdout.flush()

stopLocalT1(amc, options.gtx)
writeAllVFATs(amc, options.gtx, "ContReg0",    0x36, mask)

myF.cd()
myT.Write()
myF.Close()




