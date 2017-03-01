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

(options, args) = parser.parse_args()

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

filename = options.filename

biasAllVFATs(testSuite.glib,options.gtx,0x0,enable=False)
writeAllVFATs(testSuite.glib, options.gtx, "VThreshold1", 100, 0)
#writeVFAT(testSuite.glib, options.gtx, 0, "VThreshold1", 40)
#writeVFAT(testSuite.glib, options.gtx, 1, "VThreshold1", 25)
#writeVFAT(testSuite.glib, options.gtx, 2, "VThreshold1", 20)
#writeVFAT(testSuite.glib, options.gtx, 3, "VThreshold1", 16)
#writeVFAT(testSuite.glib, options.gtx, 6, "VThreshold1", 58)
#writeVFAT(testSuite.glib, options.gtx, 7, "VThreshold1", 60)
#writeVFAT(testSuite.glib, options.gtx, 8, "VThreshold1", 60)
#writeVFAT(testSuite.glib, options.gtx, 9, "VThreshold1", 20)
#writeVFAT(testSuite.glib, options.gtx, 10, "VThreshold1", 19)
#writeVFAT(testSuite.glib, options.gtx, 11, "VThreshold1", 26)
#writeVFAT(testSuite.glib, options.gtx, 14, "VThreshold1", 50)
#writeVFAT(testSuite.glib, options.gtx, 15, "VThreshold1", 63)
#writeVFAT(testSuite.glib, options.gtx, 16, "VThreshold1", 23)
#writeVFAT(testSuite.glib, options.gtx, 17, "VThreshold1", 17)
#writeVFAT(testSuite.glib, options.gtx, 18, "VThreshold1", 20)
#writeVFAT(testSuite.glib, options.gtx, 19, "VThreshold1", 43)
#writeVFAT(testSuite.glib, options.gtx, 22, "VThreshold1", 55)
#writeVFAT(testSuite.glib, options.gtx, 23, "VThreshold1", 62)

inF = TFile(filename)

for event in inF.scurveTree :
    if event.vcal == 10 :
        writeVFAT(testSuite.glib,options.gtx,int(event.vfatN),"VFATChannels.ChanReg%d"%(int(event.vfatCH)+1),int(event.trimDAC))
        if event.vfatCH == 10 : writeVFAT(testSuite.glib, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),0)


print 'Chamber Configured'







