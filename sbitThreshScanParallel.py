#!/bin/env python
"""
Script to measure sbit rate as a function of CFG_THR_ARM_DAC
By: Brian Dorney (brian.l.dorney@cern.ch)
    Evaldas Juska (evaldas.juska@cern.ch)
"""

import sys, os
from array import array
from ctypes import *

from gempython.tools.vfat_user_functions_xhal import *

from qcoptions import parser

parser.add_option("--arm", action="store_true", dest="scanARM",
                  help="Use only the arming comparator instead of the CFD", metavar="scanARM")
parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                  help="Specify minimum channel number to scan", metavar="chMin")
parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                  help="Specify maximum channel number to scan", metavar="chMax")
parser.add_option("-f", "--filename", type="string", dest="filename", default="SBitRateData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--perchannel", action="store_true", dest="perchannel",
                  help="Run a per-channel sbit rate scan", metavar="perchannel")
#parser.add_option("--zcc", action="store_true", dest="scanZCC",
#                  help="V3 Electronics only, scan the threshold on the ZCC instead of the ARM comparator", metavar="scanZCC")

parser.set_defaults(stepSize=2)
(options, args) = parser.parse_args()

remainder = (options.scanmax-options.scanmin+1) % options.stepSize
if remainder != 0:
    options.scanmax = options.scanmax + remainder
    print "extending scanmax to: ", options.scanmax

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')
myT = r.TTree('rateTree','Tree Holding CMS GEM Sbit Rate Data')

isCFD = array( 'i', [0] )
isCFD[0] = 1
myT.Branch( 'isCFD', isCFD, 'isCFD/I' )
vth = array( 'i', [ 0 ] )
myT.Branch( 'vth', vth, 'vth/I' )
Rate = array( 'd', [ 0. ] )
myT.Branch( 'Rate', Rate, 'Rate/D' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx
utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import datetime,time
utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

mask = options.vfatmask

try:
    vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)
    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
        print("Parent AMC Major FW Version: %i"%(self.parentAMC.fwVersion))
        print("Only implemented for v3 electronics, exiting")
        sys.exit(os.EX_USAGE)
    
    #Place chips into run mode & set MSPL
    vfatBoard.setRunModeAll(mask, True, options.debug)
    vfatBoard.setVFATMSPLAll(mask, options.MSPL, options.debug)
    
    #Store original CFG_SEL_COMP_MODE
    vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", mask)
    selCompVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
        range(0,24)))
    
    #Store original CFG_FORCE_EN_ZCC
    vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", mask)
    forceEnZCCVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
        range(0,24)))
    
    if options.scanARM: #Use arming comparator
        isCFD[0]=0
        vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE",0x1,mask)
        vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC",0x0,mask)
    else:               #Use CFD Mode (default)
        vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE",0x0,mask)
        vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC",0x0,mask)

    #determine total time in hours
    if options.perchannel:
        totalTime=(options.scanmax-options.scanmin)*(options.chMax-options.chMin)*(1./3600.)
        
        print("I see you've asked for a perchannel scan")
        print("Right now this is done in series, are you sure you want to continue?")
        print("I expect this will take: %f hours"%totalTime)
        
        bInputUnderstood=False
        performTest=raw_input("Do you want to continue? (yes/no)")
        while(not bInputUnderstood):
            performTest=performTest.upper()
            if performTest == "NO":
                print("Okay, exiting!")
                print("Please run again and change the '--chMin', '--chMax', '--scanmin', and/or '--scanmax' parameters")
                sys.exit(os.EX_USAGE)
            elif performTest == "YES":
                bInputUnderstood = True
                break;
            else:
                performTest=raw_input("input not understood, please enter 'yes' or 'no'")

    #Perform Scan
    scanReg = "THR_ARM_DAC"
    scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
    scanDataDAC = (c_uint32 * scanDataSizeVFAT)()
    scanDataRate = (c_uint32 * scanDataSizeVFAT)()
    scanDataRatePerVFAT = 24 * (c_uint32 * scanDataSizeVFAT)()
    
    # Scan over all channels or just a channel OR???
    if options.perchannel:
        for chan in range(options.chMin,options.chMax+1):
            print("scanning %s of VFAT%i channel %i"%(scanReg, vfat, chan))

            # Perform the scan
            rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=mask, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT, 
                                                             dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, 
                                                             chan=chan, scanReg=scanReg, isParallel=True)
             
            if rpcResp != 0:
                print("sbit rate scan for VFAT%i channel %i failed"%(vfat,chan))
                #raise Exception('RPC response was non-zero, sbit rate scan for VFAT%i failed'%vfat)
                continue #For now just skip instead of crash
    
            #Store Output Data - Per VFAT
            if options.debug:
                print("VFAT\tChan\tDAC\tRate")
            for vfat in range(0,23):
                for idx in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                    try:
                        Rate[0] = scanDataRatePerVFAT[idx]
                        vfatCH[0] = chan
                        vfatN[0] = vfat
                        vth[0] = scanDataDAC[idx-vfat*scanDataSizeVFAT]

                        if options.debug:
                            print("%i\t%i\t%i\t%i"%(vfat,chan,scanDataDAC[idx-vfat*scanDataSizeVFAT],scanDataRatePerVFAT[idx]))
                    except IndexError:
                        Rate[0] = -99
                        vfatCH[0]= chan
                        vfatN[0] = vfat
                        vth[0] = options.scanmin+1+options.stepSize*(idx-vfat*scanDataSizeVFAT)
                        print("Unable to index data for VFAT%i idx %i expected DAC val"%(vfat, idx, vth[0]))
                    finally:
                        myT.Fill()

            # Store Output Data - Overall
            for idx in range(0, scanDataSizeVFAT):
                try:
                    Rate[0] = scanDataRate[idx]
                    vfatCH[0] = chan
                    vfatN[0] = 24
                    vth[0] = scanDataDAC[idx]
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0] = chan
                    vfatN[0] = 24
                    vth[0] = options.scanmin+1+options.stepSize*(idx)
                finally:
                    myT.Fill()

            myT.AutoSave("SaveSelf")
    else:
        print("scanning %s of VFAT%i for all channels"%(scanReg, vfat))
        
        # Perform the scan
        rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=mask, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT,
                                                         dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, 
                                                         scanReg=scanReg, isParallel=True)
         
        if rpcResp != 0:
            print("sbit rate scan for VFAT%i failed"%vfat)
            raise Exception('RPC response was non-zero, sbit rate scan for VFAT%i failed'%vfat)

        # Store Output Data - Per VFAT
        if options.debug:
            print("VFAT\tDAC\tRate")
        for vfat in range(0,23):
            for idx in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                try:
                    Rate[0] = scanDataRate[idx]
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = scanDataDAC[idx-vfat*scanDataSizeVFAT]

                    if options.debug:
                        print("%i\t%i\t%i"%(vfat,scanDataDAC[idx],scanDataRate[idx]))
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = options.scanmin+1+options.stepSize*(idx-vfat*scanDataSizeVFAT)
                    print("Unable to index data for VFAT%i idx %i expected DAC val"%(vfat, idx, vth[0]))
                finally:
                    myT.Fill()
        
            # Store Output Data - Overall
            for idx in range(0, scanDataSizeVFAT):
                try:
                    Rate[0] = scanDataRate[idx]
                    vfatCH[0] = 128
                    vfatN[0] = 24
                    vth[0] = scanDataDAC[idx]
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0] = 128
                    vfatN[0] = 24
                    vth[0] = options.scanmin+1+options.stepSize*(idx)
                finally:
                    myT.Fill()
        
        myT.AutoSave("SaveSelf")

    # Take chips out of run mode
    vfatBoard.setRunModeAll(mask, False, options.debug)
  
    # Return to original comparator settings
    for key,val in selCompVals_orig.iteritems():
        if (mask >> key) & 0x1: continue
        vfatBoard.writeVFAT(key,"CFG_SEL_COMP_MODE",val)
    for key,val in forceEnZCCVals_orig.iteritems():
        if (mask >> key) & 0x1: continue
        vfatBoard.writeVFAT(key,"CFG_FORCE_EN_ZCC",val)

except Exception as e:
    myT.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    myT.Write()
    myF.Close()
