#!/usr/bin/env python

from GEMDAQTestSuite import *

from optparse import OptionParser
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
parser.add_option("--tests", type="string", dest="tests",default="A,B,C,D,E,F,G,H,I,J",
                  help="Tests to run, default is all", metavar="tests")

parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

(options, args) = parser.parse_args()

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
