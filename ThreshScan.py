#!/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 09:28:14 2016

@author: Hugo
@modifiedby: Jared
@modifiedby: Christine
"""

import sys, os, random, time
from optparse import OptionParser

if __name__ == "__main__":
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
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Write the data to disk when testing the rate", metavar="debug")

    parser.add_option("--doLatency", action="store_true", dest="doLatency",
                      metavar="doLatency",
                      help="[OPTIONAL] Run latency scan to determine the latency value")

    parser.add_option("--QC3test", action="store_true", dest="doQC3",
                      metavar="doQC3",
                      help="[OPTIONAL] Run a shortened test after covers have been applied")

    (options, args) = parser.parse_args()

    import subprocess,datetime
    startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
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
        thresh_abs=0.0,
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
        t1_interval=150,
        t1_delay=10
        )

    sys.stdout.flush()
    ####################################################

    testsToRun = "E"

    print "Running %s on AMC%02d  OH%02d"%(testsToRun,options.slot,options.gtx)

    testSuite = GEMDAQTestSuite(slot=options.slot,
                                gtx=options.gtx,
                                tests=testsToRun,
                                test_params=test_params,
                                debug=options.debug)

    testSuite.runSelectedTests()
    print testSuite.presentVFAT2sSingle
    for vfat in testSuite.presentVFAT2sSingle:
        print "Running threshold scan on VFAT %d"%(vfat)
        setRunMode(testSuite.glib,options.gtx,vfat,enable=True,debug=options.debug)
        sCurveTests = VFATSCurveTools(glib=testSuite.glib,
                                      slot=vfat,
                                      gtx=options.gtx,
                                      scan_params=scan_params,
                                      doLatency=options.doLatency,
                                      debug=options.debug)
        
        data_threshold = sCurveTests.scanThresholdByVFAT(vfat,debug=options.debug)
        setRunMode(testSuite.glib,options.gtx,vfat,enable=False,debug=options.debug)
        if options.debug:
            print "Length of returned data_threshold = %d"%(len(data_threshold))
            pass
        threshold = 0
        noise = 100*(data_threshold[0] & 0xffffff)/(1.*sCurveTests.N_EVENTS_THRESH)
        if options.debug:
            print "%d = %3.4f"%(((data_threshold[0] & 0xff000000) >> 24), noise)
            pass

        for d in range (1,len(data_threshold)-1):
            noise     = 100*(data_threshold[d  ] & 0xffffff)/(1.*sCurveTests.N_EVENTS_THRESH)
            lastnoise = 100*(data_threshold[d-1] & 0xffffff)/(1.*sCurveTests.N_EVENTS_THRESH)
            nextnoise = 100*(data_threshold[d+1] & 0xffffff)/(1.*sCurveTests.N_EVENTS_THRESH)

            passAbs     = (noise) <= sCurveTests.THRESH_ABS
            passLastRel = (lastnoise - noise) < sCurveTests.THRESH_REL
            passNextRel = abs(noise - nextnoise) < sCurveTests.THRESH_REL

            if options.debug:
                print "%d = %3.4f"%(((data_threshold[d] & 0xff000000) >> 24), noise)
                pass
            if passAbs and passLastRel and passNextRel:
                # why is the threshold set to the previous value?                                                                                                        
                threshold = (data_threshold[d] >> 24 )
                # setVFATThreshold(testSuite.glib,testSuite.gtx,vfat,vt1=(threshold),vt2=0)
                print "Threshold set to: %d"%(threshold)
                break
            pass
        # self.z.close()                                                                                                                                                 

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print s.getvalue()
