#!/bin/env python


# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 09:28:14 2016

@author: Hugo
@modifiedby: Jared
@modifiedby: Christine
@modifiedby: Reyer
@modifiedby: Geng
"""

#import sys, os, random, time
from GEMDAQTestSuite import *
from vfat_functions_uhal import *
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
parser.add_option("--tests", type="string", dest="tests",default="A,B,C,D,E",
                  help="Tests to run, default is all", metavar="tests")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

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

    ########################## The Script ################################
THRESH_ABS = 0.1
THRESH_REL = 0.05
THRESH_MAX = 254
THRESH_MIN = 0
SCURVE_MIN = 0
SCURVE_MAX = 254
N_EVENTS = 1000.00
N_EVENTS_SCURVE = 1000.00
CHAN_MIN = 0
CHAN_MAX = 128

TotVCal = {}
VCal_ref  = {}

for port in testSuite.presentVFAT2sSingle:
    TotVCal[str(port)+"0"] = []
    TotVCal[str(port)+"16"] = []
    TotVCal[str(port)+"31"] = []
    TotFoundVCal = []

    VCal_ref[str(port)+"0"]   = 0
    VCal_ref[str(port)+"31"]  = 0
    VCal_ref[str(port)+"avg"] = 0


pass



print "------------------------------------------------------"
print "--------------- Testing All VFAT2s-----------------"
print "------------------------------------------------------"

#Creating all the files
for port in testSuite.presentVFAT2sSingle:
    f = open("%s_Data_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),port,testSuite.chipIDs[port]&0xffff),'w')
    m = open("%s_SCurve_by_channel_VFAT2_%d_ID_0x%04x"%(str(Date),port,testSuite.chipIDs[port]&0xffff),'w')
    z = open("%s_Setting_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),port,testSuite.chipIDs[port]&0xffff),'w')
    h = open("%s_VCal_VFAT2_%d_ID_0x%04x"%(str(Date),port,testSuite.chipIDs[port]&0xffff),'w')
    g = open("%s_TRIM_DAC_value_VFAT_%d_ID_0x%04x"%(str(Date),port,testSuite.chipIDs[port]&0xffff),'w')
    z.write(time.strftime("%Y/%m/%d") +"-" +time.strftime("%H:%M:%S")+"\n")
    z.write("chip ID: 0x%04x"%(testSuite.chipIDs[port])+"\n")
    f.close()
    m.close()
    z.close()
    h.close()
    g.close()
    pass
    ################## Threshold Scan For All VFAT2 #########################
biasAllVFATs(testSuite.glib, options.gtx, 0, enable = True, debug = options.debug) #Not sure this should be set
configureScanModule(testSuite.glib, options.gtx, 0, 0, scanmin = THRESH_MIN, scanmax = THRESH_MAX, numtrigs = int(N_EVENTS), useUltra = True, debug = options.debug)
printScanConfiguration(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
startScanModule(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
UltraResults = getUltraScanResults(testSuite.glib, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)

for n in testSuite.presentVFAT2sSingle:
    f = open("%s_Data_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'a')
    z = open("%s_Setting_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'a')
    data_threshold = UltraResults[n]
    print "length of returned data_threshold = %d"%(len(data_threshold))
    threshold = 0
    noise = 100*(data_threshold[0] & 0xffffff)/(1.*N_EVENTS)
    if options.debug:
        print "First data word: 0x%08x"%(data_threshold[0])
        pass
    print "%d = %3.4f"%(((data_threshold[0] & 0xff000000) >> 24), noise)
    for d in range (1,len(data_threshold)-1):
        noise     = 100*(data_threshold[d  ] & 0xffffff)/(1.*N_EVENTS)
        lastnoise = 100*(data_threshold[d-1] & 0xffffff)/(1.*N_EVENTS)
        nextnoise = 100*(data_threshold[d+1] & 0xffffff)/(1.*N_EVENTS)
        
        passAbs     = (noise) < THRESH_ABS
        passLastRel = (lastnoise - noise) < THRESH_REL
        passNextRel = abs(noise - nextnoise) < THRESH_REL
        
        print "%d = %3.4f"%(((data_threshold[d] & 0xff000000) >> 24), noise)
        if passAbs and passLastRel and passNextRel:
            # why is the threshold set to the previous value?
            threshold = (data_threshold[d] >> 24 )
            setVFATThreshold(testSuite.glib,options.gtx,n,vt1=(threshold),vt2=0)
            print "Threshold set to: %d"%(threshold)
            f.write("Threshold set to: %d\n"%(threshold))
            z.write("vthreshold1: %d\n"%(threshold))
            break
        pass
# z.close()
    
    if threshold == 0 or threshold == 255:
        print "ignored"
        for d in range (0,len(data_threshold)):
            f.write("%d\t%f\n"%((data_threshold[d] & 0xff000000) >> 24,
                                     100*(data_threshold[d] & 0xffffff)/(1.*N_EVENTS)))
            pass
        pass

    for d in range (0,len(data_threshold)):
        f.write("%d\t%f\n"%((data_threshold[d] & 0xff000000) >> 24,
                                 100*(data_threshold[d] & 0xffffff)/(1.*N_EVENTS)))
        pass
    f.close()
    pass
    ################## S-curve by channel ######################

#enable triggers
configureLocalT1(testSuite.glib, options.gtx, 1, 0, 40, 200, 0, options.debug)
startLocalT1(testSuite.glib, options.gtx)
    #### With TRIM DAC to 0
for channel in range(CHAN_MIN, CHAN_MAX):
    for trim in [0,16,31]:
        writeAllVFATs(testSuite.glib, options.gtx, "VFATChannels.ChanReg%d"%(channel+1), 64+trim)
        configureScanModule(testSuite.glib, options.gtx, 3, 0, channel = channel, scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS_SCURVE), useUltra = True, debug = options.debug)
        printScanConfiguration(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
        startScanModule(testSuite.glib, options.gtx, useUltra = True, debug = options.debug)
        SCurve_Ultra_Results = getUltraScanResults(testSuite.glib, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)

        for n in testSuite.presentVFAT2sSingle:
            m = open("%s_SCurve_by_channel_VFAT2_%d_ID_0x%04x"%(str(Date),port,testSuite.chipIDs[n]&0xffff),'a')
            print "---------------- S-Curve data trimDAC %2d --------------------"%(trim)
            data_scurve = SCurve_Ultra_Results[n] 
            if (trim == 16):
                m.write("SCurve_%d\n"%(channel))
                pass
            try:
                if options.debug:
                    print "Length of returned data_scurve = %d"%(len(data_scurve))
                    print "First data word: 0x%08x"%(data_scurve[0])
                    for d in range (0,len(data_scurve)):
                        "%d ==> %3.4f"%((data_scurve[d] & 0xff000000) >> 24,
                                        (data_scurve[d] & 0xffffff) / (1.*N_EVENTS_SCURVE))
                        pass
                    pass
                passed = False
                for d in range (0, len(data_scurve)):
                    VCal = (data_scurve[d] & 0xff000000) >> 24
                    Eff  = (data_scurve[d] & 0xffffff) / (1.*N_EVENTS_SCURVE)
                    if options.debug:
                        print "%d => %3.4f"%(VCal,Eff)
                        pass
                    if (Eff >= 0.48 and not passed):
                        if not passed:
                            print "%d => %3.4f"%(VCal,Eff)
                            TotVCal[str(n)+"%s"%(trim)].append(VCal)
                            pass
                        passed = True
                        if trim in [0,31]:
                            break # stop scanning for high and low trim values
                        pass
                    if (trim == 16):
                        m.write("%d\t%f\n"%(VCal,Eff))  # write to file for trim == 16
                        pass
                    pass
                
            except:
                ex = sys.exc_info()[0]
                print "Caught exception: %s"%(ex)
                print "Error while reading the data, they will be ignored"
                m.close()
                pass
            m.close()
            pass
        writeAllVFATs(testSuite.glib, options.gtx, "VFATChannels.ChanReg%d"%(channel+1), trim)
        pass
    pass
print "------Second Debug ----" + str(channel)
    ################## Adjust the trim for each channel ######################
    #    if options.doQC3:
    #        continue
sys.exit()
print
print "------------------------ TrimDAC routine ------------------------"
print
for channel in range(CHAN_MIN, CHAN_MAX):
    if debug:
        for trim in [0,16,31]:
            print "TotVCal[%d](length = %d) = %s"%(trim,
                                                   len(TotVCal["%d"%(trim)]),
                                                       TotVCal["%d"%(trim)])
            pass
        pass
    for n in testSuite.presentVFAT2sSingle:
        h=open("%s_VCal_VFAT2_%d_ID_0x%04x"%(str(Date),n,testSuite.chipIDs[n]&0xffff),'a')
        try:
            VCal_ref[str(n)+"0"] = sum(TotVCal[str(n)+"0"])/len(TotVCal[str(n)+"0"])
            h.write(str(TotVCal0[str(n)+"0"])+"\n")
            VCal_ref[str(n)+"31"] = sum(TotVCal[str(n)+"31"])/len(TotVCal[str(n)+"31"])
            h.write(str(TotVCal[str(n)+"31"])+"\n")
            VCal_ref[str(n)+"avg"] = (VCal_ref[str(n)+"0"] + VCal_ref[str(n)+"31"])/2
            print "VCal_ref0", VCal_ref[str(n)+"0"]
            print "VCal_ref31", VCal_ref[str(n)+"31"]
        except:
            ex = sys.exc_info()[0]
            print "Caught exception: %s"%(ex)
            print "S-Curve did not work"
            h.close()
        pass
        TRIM_IT = [0] * 23
        print "TrimDAC Channel%d" %channel
        trimDAC = [16] * 23
        foundGood = False
        
        while (foundGood == False):


            while (glib.get("ultra_status") != 0): i = 1
            for n in testSuite.presentVFAT2sSingle:
                regValue = (1 << 6) + trimDAC[n]
                f = open("%s_Data_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'a')
                g = open("%s_TRIM_DAC_value_VFAT_%d_ID_0x%04x"%(str(Date),n,testSuite.chipIDs[n]&0xffff),'a')
                data_trim = glib.fifoRead('ultra_data'+str(n), VCAL_MAX - VCAL_MIN)
                try:
                    for d in data_trim:
                        Eff = (d & 0xffffff) / N_EVENTS_SCURVE
                        VCal = (d & 0xff000000) >> 24
                        if (Eff >= 0.48):
                            print VCal, " => ",Eff
                            foundVCal = VCal
                            break
                        pass
                    pass
                except:
                    print "Error while reading the data, they will be ignored"
                    continue
                
                if (foundVCal > VCal_ref[n] and TRIM_IT[n] < MAX_TRIM_IT and trimDAC[n] < 31):
                    trimDAC[n] += 1
                    TRIM_IT[n] +=1
                elif (foundVCal < VCal_ref[n] and TRIM_IT[n] < MAX_TRIM_IT and trimDAC[n] > 0):
                    trimDAC[n] -= 1
                    TRIM_IT[n] +=1
                else:
                    g.write(str(trimDAC[n])+"\n")
                    TotFoundVCal.append(foundVCal)
                    f.write("S_CURVE_"+str(channel)+"\n")
                    for d in data_trim:
                        f.write(str((d & 0xff000000) >> 24)+"\n")
                        f.write(str((d & 0xffffff)/N_EVENTS_TRIM)+"\n")
                        pass
                    break
                pass
            g.close()
            f.close()
            pass
        glib.set("ei2c_reset", 0)
        glib.set(regName, 0) # disable cal pulse to channel                                                                                                                                             
        m.close()
        h.write(str(TotFoundVCal)+"\n")
        h.close()
        pass
    VCalList = []
    minVcal = 0
    ################# Set all the Trim_DAC to the right value #################
    for port in presentVFAT2Single:
        g=open("%s_TRIM_DAC_value_VFAT_%d_ID_0x%04x"%(str(Date),port,testSuite.chipIDs[port]&0xffff),'r')
        #g=open(str(Date)+"_TRIM_DAC_value_VFAT_"+str(port)+"_ID_"+ str(testSuite.chipIDs[port]&0xff),'r')
        for channel in range(CHAN_MIN, CHAN_MAX):
            if options.debug:
                if channel > 10:
                    continue
                pass
            regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
            trimDAC = (g.readline()).rstrip('\n')
            print trimDAC
            regValue = int(trimDAC)
            glib.set(regName, regValue)
            pass
        g.close()
        pass
    ########################## Final threshold by VFAT2 ######################
    #        f.write("second_threshold\n")
    glib.set('ultra_reset', 1)
    glib.set('ultra_mode', 0)
    glib.set('ultra_min', 0)
    glib.set('ultra_max', 255)
    glib.set('ultra_step', 1)
    glib.set('ultra_n', N_EVENTS)
    glib.set('ultra_toggle', 1)
    while (glib.get("ultra_status") != 0): r = 1
    for n in range(0, 24):
        f = open("%s_Data_GLIB_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'a')
        f.write("second_threshold\n")
        data = glib.fifoRead('ultra_data'+str(n), 255)
        for d in data:
            f.write(str((d & 0xff000000) >> 24)+"\n")
            f.write(str(100*(d & 0xffffff)/N_EVENTS)+"\n")
            pass
        f.close()
        pass
    pass
pr.disable()
s = StringIO.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print s.getvalue()

