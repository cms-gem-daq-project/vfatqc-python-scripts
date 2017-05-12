#!/bin/env python
"""
Script to take latency data using OH BX delay counter
By: Jared Sturdy  (sturdy@cern.ch)
    Cameron Bravo (c.bravo@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("--filename", type="string", dest="filename", default="LatencyData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)
parser.add_option("--mspl", type="int", dest="mspl",
                  help="VThreshold1 DAC value for all VFATs", metavar="mspl", default=1)

parser.set_defaults(nevts=1000)

(options, args) = parser.parse_args()
uhal.setLogLevelTo( uhal.LogLevel.WARNING )

if options.mspl not in range(1,9):
    print "Invalid MSPL specified: %d, must be in range [1,8]"%(options.mspl)
    exit(1)

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.INFO )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree
filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('latencyTree','Tree Holding CMS GEM Latency Data')

Dly = array( 'i', [ -1 ] )
myT.Branch( 'Dly', Dly, 'Dly/I' )
vfatN = array( 'i', [ -1 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vth = array( 'i', [ 0 ] )
myT.Branch( 'vth', vth, 'vth/I' )
vth1 = array( 'i', [ 0 ] )
myT.Branch( 'vth1', vth1, 'vth1/I' )
vth2 = array( 'i', [ 0 ] )
myT.Branch( 'vth2', vth2, 'vth2/I' )
mspl = array( 'i', [ -1 ] )
myT.Branch( 'mspl', mspl, 'mspl/I' )
link = array( 'i', [ -1 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx
utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import time
utime[0] = int(time.time())

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)
seenTriggers = 0

try:
    print "Setting trigger source"
    # setTriggerSource(ohboard,options.gtx,0x0) # GTX
    setTriggerSource(ohboard,options.gtx,0x5) # GBT

    print "Setting run mode"
    writeAllVFATs(ohboard, options.gtx, "ContReg0",   0x37)
    print "Setting MSPL to %d"%(options.mspl)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",    ((options.mspl-1)<<4))
    # writeAllVFATs(ohboard, options.gtx, "VThreshold1", options.vt1)

    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold1", mask)
    vt1vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vals  = readAllVFATs(ohboard, options.gtx, "VThreshold2", mask)
    vt2vals =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
                        range(0,24)))
    vthvals =  dict(map(lambda slotID: (slotID, vt2vals[slotID]-vt2vals[slotID]),
                        range(0,24)))
    vals = readAllVFATs(ohboard, options.gtx, "ContReg2",    mask)
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
                Dly[0]   = dlyValue
                vfatN[0] = vfat
                mspl[0]  = msplvals[vfatN]
                vth1[0]  = vt1vals[vfatN]
                vth2[0]  = vt2vals[vfatN]
                vth[0]   = vthvals[vfatN]
                writeRegister(ohboard,"%s.VFAT%d_LAT_BX.RESET"%(baseNode,vfat),0x1)
                myT.Fill()
                pass
            if (seenTriggers%100 == 0):
                print "Saw %d triggers"%(seenTriggers)
                pass
            pass
        myT.AutoSave("SaveSelf")
        sys.stdout.flush()
        if seenTriggers > options.nevts:
            print "Saw %d triggers, exiting"%(seenTriggers)
            sys.stdout.flush()
            break

except Exception as e:
    myT.AutoSave("SaveSelf")
    print "An exception occurred", e
    sys.stdout.flush()
finally:
    myF.cd()
    myT.Write()
    myF.Close()

