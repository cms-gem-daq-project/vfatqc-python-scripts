#!/bin/env python
"""
Script to set trimdac values on a chamber
By: Christine McLean (ch.mclean@cern.ch), Cameron Bravo (c.bravo@cern.ch), Elizabeth Starling (elizabeth.starling@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.nesteddict import nesteddict as ndict
from gempython.utils.wrappers import runCommand, envCheck
from mapping.chamberInfo import chamber_config

from qcoptions import parser
parser.add_option("--calFile", type="string", dest="calFile", default=None,
                  help="File specifying CAL_DAC/VCAL to fC equations per VFAT",
                  metavar="calFile")
parser.add_option("--calSF", type="int", dest = "calSF", default = 0,
                  help="V3 electroncis only. Value of the CFG_CAL_FS register", metavar="calSF")
parser.add_option("--dirPath", type="string", dest="dirPath", default=None,
                  help="Specify the path where the scan data should be stored", metavar="dirPath")
parser.add_option("--latency", type="int", dest = "latency", default = 37,
                  help="Specify Latency", metavar="latency")
parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                  help="V3 electronics only. Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                  metavar="voltageStepPulse")
(options, args) = parser.parse_args()

rangeFile = options.rangeFile
ztrim = options.ztrim
print 'trimming at z = %f'%ztrim

envCheck('DATA_PATH')
envCheck('BUILD_HOME')

dataPath = os.getenv('DATA_PATH')

from fitting.fitScanData import fitScanData
import subprocess,datetime
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime

if options.dirPath == None: 
    dirPath = '%s/%s/trimming/z%f/%s'%(dataPath,chamber_config[options.gtx],ztrim,startTime)
else: 
    dirPath = options.dirPath

# Declare the hardware board and bias all vfats
vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)
if options.gtx in chamber_vfatDACSettings.keys():
    print "Configuring VFATs with chamber_vfatDACSettings dictionary values"
    for key in chamber_vfatDACSettings[options.gtx]:
        vfatBoard.paramsDefVals[key] = chamber_vfatDACSettings[options.gtx][key]
vfatBoard.biasAllVFATs(options.vfatmask)
print 'biased VFATs'

CHAN_MIN = 0
CHAN_MAX = 128

masks = ndict()
for vfat in range(0,24):
    for ch in range(CHAN_MIN,CHAN_MAX):
        masks[vfat][ch] = False

#Find trimRange for each VFAT
trimVcal = ndict()
trimCH   = ndict()
goodSup  = ndict()
goodInf  = ndict()
for vfat in range(0,24):
    trimVcal[vfat] = 0
    trimCH[vfat] = 0
    goodSup[vfat] = -99
    goodInf[vfat] = -99

###############
# TRIMDAC = 0
###############
# Configure for initial scan
# Zero all channel registers for an initial starting point
for chan in range(0,128):
    vfatBoard.setChannelRegisterAll(chan)

# Scurve scan with trimdac set to 0
filename0 = "%s/SCurveData_trimdac0_range0.root"%dirPath
cmd = [ "ultraScurve.py",
        "--shelf=%i"%(options.shelf),
        "-s%d"%(options.slot),
        "-g%d"%(options.gtx),
        "--filename=%s"%(filename0),
        "--vfatmask=0x%x"%(options.vfatmask),
        "--nevts=%i"%(options.nevts),
        "--calFile=%s"(options.calFile),
        "--calSF=%i"%(options.calSF),
        "--latency=%i"%(options.latency)
        ]
if options.voltageStepPulse:
    cms.append("--voltageStepPulse")
if options.debug:
    cmd.append("--debug")
runCommand(cmd)

muFits_0 = fitScanData(filename0, isVFAT3=True)
for vfat in range(0,24):
    for ch in range(CHAN_MIN,CHAN_MAX):
        if muFits_0[4][vfat][ch] < 0.1: masks[vfat][ch] = True

#calculate the sup and set trimVcal
sup = ndict()
supCH = ndict()
for vfat in range(0,24):
    sup[vfat] = 999.0
    supCH[vfat] = -1
    for ch in range(CHAN_MIN,CHAN_MAX):
        if(masks[vfat][ch]): continue
        if(muFits_0[0][vfat][ch] - ztrim*muFits_0[1][vfat][ch] < sup[vfat] and muFits_0[0][vfat][ch] - ztrim*muFits_0[1][vfat][ch] > 0.1): 
            sup[vfat] = muFits_0[0][vfat][ch] - ztrim*muFits_0[1][vfat][ch]
            supCH[vfat] = ch
    goodSup[vfat] = sup[vfat]
    trimVcal[vfat] = sup[vfat]
    trimCH[vfat] = supCH[vfat]
    
#Init trimDACs to all zeros
trimDACs = ndict()
for vfat in range(0,24):
    for ch in range(CHAN_MIN,CHAN_MAX):
        trimDACs[vfat][ch] = 0

# This is a binary search to set each channel's trimDAC
for i in range(0,5):
    # First write this steps values to the VFATs
    for vfat in range(0,24):
        for ch in range(CHAN_MIN,CHAN_MAX):
            trimDACs[vfat][ch] += pow(2,4-i)
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(ch),trimDACs[vfat][ch],options.debug)
    # Run an SCurve
    filenameBS = "%s/SCurveData_binarySearch%i.root"%(dirPath,i)
    cmd = [ "ultraScurve.py",
            "--shelf=%i"%(options.shelf),
            "-s%d"%(options.slot),
            "-g%d"%(options.gtx),
            "--filename=%s"%(filenameBS),
            "--vfatmask=0x%x"%(options.vfatmask),
            "--nevts=%i"%(options.nevts)]
    if options.debug:
        cmd.append("--debug")
    runCommand(cmd)

    # Fit Scurve data
    fitData = fitScanData(filenameBS)
    # Now use data to determine the new trimDAC value
    for vfat in range(0,24):
        for ch in range(CHAN_MIN,CHAN_MAX):
            if(fitData[0][vfat][ch] - ztrim*fitData[1][vfat][ch] < trimVcal[vfat]): trimDACs[vfat][ch] -= pow(2,4-i)

# Now take a scan with trimDACs found by binary search
for vfat in range(0,24):
    for ch in range(CHAN_MIN,CHAN_MAX):
        writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(ch),trimDACs[vfat][ch],options.debug)

filenameFinal = "%s/SCurveData_Trimmed.root"%dirPath
cmd = [ "ultraScurve.py",
        "--shelf=%i"%(options.shelf),
        "-s%d"%(options.slot),
        "-g%d"%(options.gtx),
        "--filename=%s"%(filenameFinal),
        "--vfatmask=0x%x"%(options.vfatmask),
        "--nevts=%i"%(options.nevts)]
if options.debug:
    cmd.append("--debug")
runCommand(cmd)

scanFilename = '%s/scanInfo.txt'%dirPath
outF = open(scanFilename,'w')
outF.write('vfat/I:tRange/I:sup/D:inf/D:trimVcal/D:trimCH/D\n')
for vfat in range(0,24):
    outF.write('%i  %i  %f  %f  %f  %i\n'%(vfat,tRanges[vfat],goodSup[vfat],goodInf[vfat],trimVcal[vfat],trimCH[vfat]))
    pass
outF.close()

exit(0)
