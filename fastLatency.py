#!/bin/env python
"""
Script to take latency data using OH BX delay counter
By: Jared Sturdy  (sturdy@cern.ch)
    Cameron Bravo (c.bravo@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_uhal import *

from gempython.vfatqc.qcoptions import parser

parser.add_option("--filename", type="string", dest="filename", default="LatencyData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)

parser.set_defaults(nevts=1000)
(options, args) = parser.parse_args()

if options.MSPL not in range(1,9):
    print "Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL)
    exit(1)

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.DEBUG )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from gempython.tools.amc_user_functions_uhal import *
amcBoard = getAMCObject(options.slot, options.shelf, options.debug)
printSystemSCAInfo(amcBoard, options.debug)
printSystemTTCInfo(amcBoard, options.debug)

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')

# Setup the output TTree
from gempython.vfatqc.treeStructure import gemTreeStructure
gemData = gemTreeStructure('latencyTree','Tree Holding CMS GEM Latency Data',scanmode.LATENCY)
gemData.setDefaults(options)
gemData.vth2[0] = options.vt2

import time
gemData.utime[0] = int(time.time())

ohboard      = getOHObject(options.slot,options.gtx,options.shelf,options.debug)
seenTriggers = 0

try:
    print "Setting trigger source"
    setTriggerSource(ohboard,options.gtx,0x5) # GBT

    print "Setting run mode"
    writeAllVFATs(ohboard, options.gtx, "ContReg0",   0x37)
    print "Setting MSPL to %d"%(options.MSPL)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",    ((options.MSPL-1)<<4))

    vfatIDvals = getAllChipIDs(ohboard, options.gtx, 0x0)
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold1", 0x0)
    vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold2", 0x0)
    vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                        range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    0x0)
    msplvals =  dict(map(lambda slotID: (slotID, (vals[slotID]>>4)&0x7),
                         range(0,24)))

    print "Setting base node before looping"
    baseNode = "GEM_AMC.OH.OH%d.COUNTERS"%(options.gtx)

    print "Resetting all VFAT counters"
    for vfat in range(0,24):
        writeRegister(ohboard,"%s.VFAT%d_LAT_BX.RESET"%(baseNode,vfat),0x1)
        pass
    while(True):
        for vfat in range(0,24):
            dlyValue = readRegister(ohboard,"%s.VFAT%d_LAT_BX"%(baseNode,vfat))
            if dlyValue > 0:
                if dlyValue < 2000:
                    # print "Saw a trigger for a hit in VFAT%02d with a delay of %d BX"%(vfat,dlyValue)
                    sys.stdout.flush()
                    seenTriggers += 1
                    pass
                gemData.Dly[0]   = dlyValue
                gemData.vfatN[0] = vfat
                gemData.mspl[0]  = msplvals[vfat]
                gemData.vfatID[0] = vfatIDvals[vfat]
                gemData.vth1[0]  = vt1vals[vfat]
                gemData.vth2[0]  = vt2vals[vfat]
                gemData.vth[0]   = vthvals[vfat]
                writeRegister(ohboard,"%s.VFAT%d_LAT_BX.RESET"%(baseNode,vfat),0x1)
                gemData.fill()
                pass
            if (seenTriggers%100 == 0):
                print "Saw %d triggers"%(seenTriggers)
                pass
            pass
        gemData.autoSave()
        sys.stdout.flush()
        if seenTriggers > options.nevts:
            print "Saw %d triggers, exiting"%(seenTriggers)
            sys.stdout.flush()
            break

except Exception as e:
    gemData.autoSave()
    print "An exception occurred", e
    sys.stdout.flush()
finally:
    myF.cd()
    gemData.write()
    myF.Close()
