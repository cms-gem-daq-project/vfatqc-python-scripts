#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
"""

#import sys, os, random, time
from array import array
from GEMDAQTestSuite import *

from qcoptions import parser

(options, args) = parser.parse_args()

test_params = TEST_PARAMS(namc=options.namc,
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

parseXML()
rpc_connect("eagle33")

setTriggerSource(testSuite.glib,options.gtx,1)
configureLocalT1(testSuite.glib, options.gtx, 1, 0, 40, 250, 0, options.debug)
print 'Starting OH T1 controller'
startLocalT1(testSuite.glib, options.gtx, options.debug)
reg=getNode("GEM_AMC.OH.OH%i.T1Controller.TOGGLE"%options.gtx)
print 'RPC register real_address ',hex(reg.real_address)
print 'RPC register address ',hex(reg.address)
#writeReg(reg,0x1)

writeAllVFATs(testSuite.glib, options.gtx, "ContReg0",    0, 0)
