#!/usr/bin/env python

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
