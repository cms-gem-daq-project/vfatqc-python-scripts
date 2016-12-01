#!/usr/bin/env python

from GEMDAQTestSuite import *
from vfat_functions_uhal import setChannelRegister
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot", default=10)
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the GLIB", metavar="gtx", default=0)
parser.add_option("-f", "--file", type="string", dest="trimfilelist",
                  help="File containing paths to MASK_TrimDACs", metavar="trimfilelist", default="TrimDACfiles.txt")

(options, args) = parser.parse_args()

trimfilelist = options.trimfilelist

testSuite = GEMDAQTestSuite(slot=options.slot,
                            gtx=options.gtx
                            
                           )

testSuite.VFAT2DetectionTest()
print testSuite.chipIDs

for port in testSuite.presentVFAT2sSingle:
    try:
        trimDACfileList = open(trimfilelist,'r')
    except:
        print "Couldn't find " + trimfilelist + "  to specify paths to TRIM_DACS"
        break
    trimDACfile = ""
    for line in trimDACfileList:
        if ("ID_0x%04x"%(testSuite.chipIDs[port]&0xffff) in line) and ("Mask_TRIM_DAC" in line):
            trimDACfile = (line).rstrip('\n')
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
        
        regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
        regline = (g.readline()).rstrip('\n')
        cc = regline.split('\t\t\t')
        chan_num = int(cc[0]) 
        trimDAC = int(cc[1])
        mask_yes = int(cc[2])
        setChannelRegister(testSuite.glib, options.gtx, port, channel, mask_yes, 0x0, trimDAC, debug = False)
        pass
