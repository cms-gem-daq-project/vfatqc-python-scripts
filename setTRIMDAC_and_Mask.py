#!/usr/bin/env python

from GEMDAQTestSuite import *
from gempython.tools.vfat_user_functions_uhal import setChannelRegister
from optparse import OptionParser

from qcoptions import parser

parser.add_option("-f", "--file", type="string", dest="trimfilelist",
                  help="File containing paths to MASK_TrimDACs", metavar="trimfilelist", default="TrimDACfiles.txt")
parser.add_option("-t", "--thresh", action="store_true", dest= "do_thresh",
                  help="Do a threshold scan before/after setting trim", metavar="do_thresh")
parser.add_option("--save", action="store_true", dest= "save",
                  help="Save Threshold Scan", metavar="save")

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
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
Date = startTime
print startTime

trimfilelist = options.trimfilelist

testSuite = GEMDAQTestSuite(slot=options.slot,gtx=options.gtx,shelf=options.shelf,debug=options.debug)

testSuite.VFAT2DetectionTest()

if options.debug:
    print testSuite.chipIDs
    pass
try:
    trimDACfileList = open(trimfilelist,'r')
except:
    print "Couldn't find " + trimfilelist + "  to specify paths to TRIM_DACS"
    sys.exit()

for port in testSuite.presentVFAT2sSingle:
    trimDACfile = ""
    for line in trimDACfileList:
        if ("ID_0x%04x"%(testSuite.chipIDs[port]&0xffff) in line) and ("Mask_TRIM_DAC" in line):
            trimDACfile = (line).rstrip('\n')
            pass
        pass
    if len(trimDACfile) < 2:
        print "Chip ID: 0x%04x"%(testSuite.chipIDs[port]&0xffff)
        trimDACfile = raw_input("> Enter Trim DAC file to read in: ")
        pass
    if len(trimDACfile) < 2:
        continue

    g=open(trimDACfile,'r') #will break here if ''

    for channel in range(0, 128):
        print "------------------- channel ", str(channel), "-------------------"
        
        regline = (g.readline()).rstrip('\n')
        cc = regline.split('\t')
        chan_num = int(cc[0]) 
        trimDAC  = int(cc[1])
        mask_yes = int(cc[2])
        setChannelRegister(testSuite.ohboard, options.gtx, port, channel, mask_yes, 0x0, trimDAC, debug = False)
        pass
    g.close()
    pass
trimDACfileList.close()

if (options.do_thresh):
    THRESH_ABS = 0.1
    THRESH_REL = 0.05
    THRESH_MAX = 250
    THRESH_MIN = 0
    N_EVENTS = 1000.00

    configureScanModule(testSuite.ohboard, options.gtx, 0, 0, scanmin = THRESH_MIN, scanmax = THRESH_MAX, numtrigs = int(N_EVENTS), useUltra = True, debug = options.debug)
    printScanConfiguration(testSuite.ohboard, options.gtx, useUltra = True, debug = options.debug)
    startScanModule(testSuite.ohboard, options.gtx, useUltra = True, debug = options.debug)
    UltraResults = getUltraScanResults(testSuite.ohboard, options.gtx, THRESH_MAX - THRESH_MIN + 1, options.debug)

    if options.debug:
        raw_input ("Press Enter to Continue")
    print
    print "Starting Preliminary Threshold Scan"
    print
    for n in testSuite.presentVFAT2sSingle:
        if options.save:
            f = open("%s_Data_AMC_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'w')
            z = open("%s_Setting_AMC_IP_%s_VFAT2_%d_ID_0x%04x"%(str(Date),str(options.slot),n,testSuite.chipIDs[n]&0xffff),'w')
            f.write("First Threshold Scan \n")
            pass
        data_threshold = UltraResults[n]
        print "On Slot Number %d"%n
        print data_threshold
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
                setVFATThreshold(testSuite.ohboard,options.gtx,n,vt1=(threshold),vt2=0)
                print "Threshold set to: %d"%(threshold)
                if options.save:
                    f.write("Threshold set to: %d\n"%(threshold))
                    z.write("vthreshold1: %d\n"%(threshold))
                    pass
                break
            
            pass
        if options.save:
            z.close()
            pass
        if d == 0 or d == 255:
            print "ignored"
            if options.save:
                f.write("Ignored \n")
                for d in range (0,len(data_threshold)):
                    f.write(str((data_threshold[d] & 0xff000000) >> 24)+"\n")
                    f.write(str(100*(data_threshold[d] & 0xffffff)/N_EVENTS)+"\n")
                    pass
                pass                                                
            continue
        if options.save:
            for d in range (0,len(data_threshold)):
                f.write(str((data_threshold[d] & 0xff000000) >> 24)+"\n")
                f.write(str(100*(data_threshold[d] & 0xffffff)/N_EVENTS)+"\n")
                pass
            f.close()
            z.close()
            pass
        pass


