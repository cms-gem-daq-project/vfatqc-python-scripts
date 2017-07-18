#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 09:28:14 2016

@author: Hugo
@modifiedby: Jared
@modifiedby: Christine
"""

import sys, os, random, time

if __name__ == "__main__":
    print "Script depreciated, use instead:"
    print "\tGEMDAQTestSuite.py,"
    print "\tultraLatency.py,"
    print "\tultraScurve.py, or"
    print "\tultraThreshold.py"
    print "Exiting"
    
    import sys
    sys.exit()

    from qcoptions import parser

    parser = OptionParser()

    (options, args) = parser.parse_args()

    if options.slot is None or options.slot not in range(1,13):
        print options.slot
        print "Must specify an AMC slot in range[1,12]"
        exit(1)
        pass

    if options.gtx is None or options.gtx not in range(0,2):
        print options.gtx
        print "Must specify an OH slot in range[0,1]"
        exit(1)
        pass

    import subprocess,datetime
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print "Start time: %s"%(startTime)

    # Unbuffer output
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    tee = subprocess.Popen(["tee", "%s-log.txt"%(startTime)], stdin=subprocess.PIPE)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

    # import cProfile, pstats, StringIO
    # pr = cProfile.Profile()
    # pr.enable()

    from GEMDAQTestSuite import *
    from VFATSCurveTools import *

    test_params = TEST_PARAMS(nglib=options.nglib,
                              noh=options.noh,
                              ni2c=options.ni2c,
                              ntrk=options.ntrk,
                              writeout=options.writeout)

    scan_params = VFAT_SCAN_PARAMS(
        thresh_abs=0.15,
        thresh_rel=0.05,
        thresh_min=0,
        thresh_max=255,
        lat_abs=98.,
        lat_min=0,
        lat_max=255,
        nev_thresh=100000,
        nev_lat=1000,
        nev_scurve=250,
        nev_trim=250,
        vcal_min=0,
        vcal_max=255,
        max_trim_it=26,
        chan_min=0,
        chan_max=128,
        def_dac=16,
        t1_n=0,
        t1_interval=210,
        t1_delay=10
        )

    sys.stdout.flush()
    ####################################################

    testsToRun = "A,B,E"

    print "Running %s on AMC%02d  OH%02d"%(testsToRun,options.slot,options.gtx)

    testSuite = GEMDAQTestSuite(slot=options.slot,
                                gtx=options.gtx,
                                shelf=options.shelf,
                                tests=testsToRun,
                                test_params=test_params)#,
                                #debug=options.debug)

    testSuite.runSelectedTests()

    for vfat in testSuite.presentVFAT2sSingle:
        if options.debug and vfat > 0:
            continue
        sCurveTests = VFATSCurveTools(ohboard=testSuite.ohboard,
                                      slot=testSuite.slot,
                                      gtx=testSuite.gtx,
                                      scan_params=scan_params,
                                      doLatency=True,
                                      debug=options.debug)
        
        sCurveTests.runScanRoutine(vfat,options.debug)
        pass

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print s.getvalue()
