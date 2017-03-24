#!/bin/env python
"""
Script to configure the VFATs on a GEM chamber
By: Cameron Bravo c.bravo@cern.ch
"""

from array import array
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("--filename", type="string", dest="filename", default=None,
                  help="Specify file containing settings information", metavar="filename")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)

(options, args) = parser.parse_args()

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.DEBUG )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree
import subprocess,datetime
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf)
print 'opened connection'

biasAllVFATs(ohboard,options.gtx,0x0,enable=False)
print 'biased VFATs'
writeAllVFATs(ohboard, options.gtx, "VThreshold1", options.vt1, 0)
print 'Set VThreshold1 to %i'%options.vt1
writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36,        0)

if options.filename != None:
    try:
        inF = TFile(options.filename)

        for event in inF.scurveTree :
            if event.vcal == 10 :
                writeVFAT(testSuite.glib,options.gtx,int(event.vfatN),"VFATChannels.ChanReg%d"%(int(event.vfatCH)),int(event.trimDAC))
                if event.vfatCH == 10 : writeVFAT(ohboard, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),0)
    except:
        print '%s does not seem to exist'%options.filename


print 'Chamber Configured'







