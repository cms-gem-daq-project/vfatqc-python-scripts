#!/bin/env python
"""
Script to configure the VFATs on a GEM chamber
By: Cameron Bravo c.bravo@cern.ch
Modified by: Eklavya Sarkar eklavya.sarkar@cern.ch
             Brian Dorney brian.l.dorney@cern.ch
"""

from array import array
from gempython.tools.vfat_user_functions_xhal import *
from gempython.gemplotting.mapping.chamberInfo import chamber_vfatDACSettings
from gempython.vfatqc.qcoptions import parser
from gempython.vfatqc.qcutilities import inputOptionsValid, setChannelRegisters
#from gempython.vfatqc.qcutilities import readBackCheck 

parser.add_option("--chConfig", type="string", dest="chConfig", default=None,
                  help="Specify file containing channel settings from anaUltraSCurve", metavar="chConfig")
parser.add_option("--compare", action="store_true", dest="compare",
                  help="When supplied with {chConfig, filename, vfatConfig} compares current reg values with those stored in input files", metavar="compare")
parser.add_option("--filename", type="string", dest="filename", default=None,
                  help="Specify file containing settings information", metavar="filename")
parser.add_option("--run", action="store_true", dest="run",
                  help="Set VFATs to run mode", metavar="run")
parser.add_option("--vfatConfig", type="string", dest="vfatConfig", default=None,
                  help="Specify file containing VFAT settings from anaUltraThreshold", metavar="vfatConfig")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 or CFG_THR_ARM_DAC value for all VFATs", metavar="vt1", default=100)
parser.add_option("--vt2", type="int", dest="vt2",
                  help="VThreshold2 DAC value for all VFATs (v2b electronics only)", metavar="vt2", default=0)
parser.add_option("--vt1bump", type="int", dest="vt1bump",
                  help="VThreshold1 DAC bump value for all VFATs", metavar="vt1bump", default=0)
parser.add_option("--zeroChan", action="store_true", dest="zeroChan",
                  help="Zero all channel registers", metavar="zeroChan")

(options, args) = parser.parse_args()

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)
print 'opened connection'

# Check options
if not inputOptionsValid(options, vfatBoard.parentOH.parentAMC):
    exit(os.EX_USAGE)
    pass

if options.gtx in chamber_vfatDACSettings.keys():
    print "Configuring VFATs with chamber_vfatDACSettings dictionary values"
    for key in chamber_vfatDACSettings[options.gtx]:
        vfatBoard.paramsDefVals[key] = chamber_vfatDACSettings[options.gtx][key]
vfatBoard.biasAllVFATs(options.vfatmask)
print 'biased VFATs'

if not options.compare:
    vfatBoard.setVFATThresholdAll(options.vfatmask, options.vt1, options.vt2)
    if vfatBoard.parentOH.parentAMC.fwVersion > 2:
        print('Set CFG_THR_ARM_DAC to %i'%options.vt1)
    else:
        print('Set VThreshold1 to %i'%options.vt1)
        print('Set VThreshold2 to %i'%options.vt2)

if options.run:
    vfatBoard.setRunModeAll(options.vfatmask, True)
    print 'VFATs set to run mode'
else:
    vfatBoard.setRunModeAll(options.vfatmask, False)

import ROOT as r
if options.filename:
    try:
        inF = r.TFile(options.filename)
        chTree = inF.Get("scurveFitTree")
        dict_readBack = {}
        if vfatBoard.parentOH.parentAMC.fwVersion > 2:
            # Need some pre-string append that is "VFAT_CHANNELS.CHANNEL"
            dict_readBack = { "trimDAC":"ARM_TRIM_AMPLITUDE", "trimPolarity":"ARM_TRIM_POLARITY", "mask":"MASK" }
        else:
            dict_readBack = { "trimDAC":"VFATChannels.ChanReg", "mask":"VFATChannels.ChanReg" }
            pass

        if not options.compare:
            print 'Configuring Channel Registers based on %s'%options.filename        
            setChannelRegisters(vfatBoard, chTree, options.vfatmask)
            pass
 
        #print 'Comparing Currently Stored Channel Registers with %s'%options.filename
        #readBackCheck(chTree, dict_readBack, ohboard, options.gtx)

    except Exception as e:
        print '%s does not seem to exist'%options.filename
        print e

if options.chConfig:
    try:
        chTree = r.TTree('chTree','Tree holding Channel Configuration Parameters')
        chTree.ReadFile(options.chConfig)
        dict_readBack = {}
        if vfatBoard.parentOH.parentAMC.fwVersion > 2:
            # Need some pre-string append that is "VFAT_CHANNELS.CHANNEL"
            # but that needs to be done in readBackCheck(...) when looping over channels
            dict_readBack = { "trimDAC":"ARM_TRIM_AMPLITUDE", "trimPolarity":"ARM_TRIM_POLARITY", "mask":"MASK" }
        else:
            dict_readBack = { "trimDAC":"VFATChannels.ChanReg", "mask":"VFATChannels.ChanReg" }

        if not options.compare:
            print 'Configuring Channel Registers based on %s'%options.chConfig
            setChannelRegisters(vfatBoard, chTree, options.vfatmask)
            pass

        #print 'Comparing Currently Stored Channel Registers with %s'%options.chConfig
        #readBackCheck(chTree, dict_readBack, ohboard, options.gtx)

    except Exception as e:
        print '%s does not seem to exist'%options.filename
        print e

if options.zeroChan:    
    print("zero'ing all channel registers")    
    rpcResp = vfatBoard.setAllChannelRegisters(vfatMask=options.vfatmask)
                
    if rpcResp != 0:
        raise Exception("RPC response was non-zero, zero'ing all channel registers failed")
    pass

if options.vfatConfig:
    try:
        vfatTree = r.TTree('vfatTree','Tree holding VFAT Configuration Parameters')
        vfatTree.ReadFile(options.vfatConfig)
        #dict_readBack = { "vt1":"VThreshold1", "trimRange":"ContReg3" }

        if not options.compare:
            print 'Configuring VFAT Registers based on %s'%options.vfatConfig

            for event in vfatTree :
                # Skip masked vfats
                if (options.vfatmask >> int(event.vfatN)) & 0x1:
                    continue
                
                # Tell user whether CFG_THR_ARM_DAC or VThreshold1 is being written
                if vfatBoard.parentOH.parentAMC.fwVersion > 2:
                    print 'Set link %d VFAT%d CFG_THR_ARM_DAC to %i'%(options.gtx,event.vfatN,event.vt1+options.vt1bump)
                else:
                    print 'Set link %d VFAT%d VThreshold1 to %i'%(options.gtx,event.vfatN,event.vt1+options.vt1bump)
                
                # Write CFG_THR_ARM_DAC or VThreshold1
                vfatBoard.setVFATThreshold(chip=int(event.vfatN), vt1=int(event.vt1+options.vt1bump))

                # Write trimRange (only supported for v2b electronics right now)
                if not (vfatBoard.parentOH.parentAMC.fwVersion > 2):
                    vfatBoard.writeVFAT(int(event.vfatN), "ContReg3", int(event.trimRange),options.debug)
        
        #print 'Comparing Curently Stored VFAT Registers with %s'%options.vfatConfig
        #if options.vt1bump != 0:
        #    print "Mismatches between write & readback valus for VThreshold1 should be exactly %i" %(options.vt1bump)
        #readBackCheck(vfatTree, dict_readBack, ohboard, options.gtx)

    except Exception as e:
        print '%s does not seem to exist'%options.filename
        print e
        
print 'Chamber Configured'
