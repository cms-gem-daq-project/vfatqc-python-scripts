#!/usr/bin/env python

from GEMDAQTestSuite import *
from vfat_functions_uhal import setChannelRegister
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot")
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the GLIB", metavar="gtx")
parser.add_option("-f", "--file", type="string", dest="trimfilelist",
                  help="File containing paths to MASK_TrimDACs", metavar="trimfilelist", default="TrimDACfiles.txt")

parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

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

trimfilelist = options.trimfilelist

testSuite = GEMDAQTestSuite(slot=options.slot,gtx=options.gtx,debug=options.debug)

testSuite.VFAT2DetectionTest()

if options.debug:
    print testSuite.chipIDs
    pass
try:
    trimDACfileList = open(trimfilelist,'r')
except:
    print "Couldn't find " + trimfilelist + "  to specify paths to TRIM_DACS"
    exit(1)

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

    trimDACfileList.close()
    g=open(trimDACfile,'r') #will break here if ''

    for channel in range(0, 127):
        
        print "------------------- channel ", str(channel), "-------------------"
        
        regline = (g.readline()).rstrip('\n')
        cc = regline.split('\t')
        chan_num = int(cc[0]) 
        trimDAC  = int(cc[1])
        mask_yes = int(cc[2])
        setChannelRegister(testSuite.glib, options.gtx, port, channel, mask_yes, 0x0, trimDAC, debug = False)
        pass
