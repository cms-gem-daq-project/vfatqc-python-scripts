#!/bin/env python
"""
Script to configure the VFATs on a GEM chamber
By: Cameron Bravo c.bravo@cern.ch
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
parser.add_option("--shelf", type="int", dest="shelf",
                  help="Which uTCA crate", metavar="shelf", default=1)
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
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")
parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData_Trimmed.root",
                          help="Specify Output Filename", metavar="filename")
parser.add_option("-v", "--vthreshold", type="int", dest="vthr",
                  help="VThreshold1 DAC value for all VFATs", metavar="vthr", default=100)

(options, args) = parser.parse_args()

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

connection_file = "file://${GEM_ADDRESS_TABLE_PATH}/connections.xml"
manager         = uhal.ConnectionManager(connection_file )
amc  = manager.getDevice( "gem.shelf%02d.amc%02d.optohybrid%02d"%(options.shelf,options.slot,options.gtx) )

print 'opened connection'

filename = options.filename

biasAllVFATs(amc,options.gtx,0x0,enable=False)
print 'biased VFATs'
writeAllVFATs(amc, options.gtx, "VThreshold1", options.vthr, 0)
print 'Set VThreshold1 to %i'%options.vthr
writeAllVFATs(amc, options.gtx, "ContReg0",    0x36, 0)

#inF = TFile(filename)

#for event in inF.scurveTree :
#    if event.vcal == 10 :
#        writeVFAT(testSuite.glib,options.gtx,int(event.vfatN),"VFATChannels.ChanReg%d"%(int(event.vfatCH)+1),int(event.trimDAC))
#        if event.vfatCH == 10 : writeVFAT(testSuite.glib, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),0)


print 'Chamber Configured'







