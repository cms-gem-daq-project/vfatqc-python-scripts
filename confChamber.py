#!/bin/env python
"""
Script to configure the VFATs on a GEM chamber
By: Cameron Bravo c.bravo@cern.ch
"""

from array import array
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData_Trimmed.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("-v", "--vthreshold", type="int", dest="vthr",
                  help="VThreshold1 DAC value for all VFATs", metavar="vthr", default=100)

(options, args) = parser.parse_args()

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.DEBUG )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree
import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf)
print 'opened connection'

filename = options.filename

biasAllVFATs(ohboard,options.gtx,0x0,enable=False)
print 'biased VFATs'
writeAllVFATs(ohboard, options.gtx, "VThreshold1", options.vthr, 0)
print 'Set VThreshold1 to %i'%options.vthr
writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, 0)

#inF = TFile(filename)

#for event in inF.scurveTree :
#    if event.vcal == 10 :
#        writeVFAT(testSuite.glib,options.gtx,int(event.vfatN),"VFATChannels.ChanReg%d"%(int(event.vfatCH)+1),int(event.trimDAC))
#        if event.vfatCH == 10 : writeVFAT(testSuite.glib, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),0)


print 'Chamber Configured'







