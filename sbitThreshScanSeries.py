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
parser.add_option("--invertVFATPos", action="store_true", dest="invertVFATPos",
                  help="Invert VFAT Position ordered, e.g. VFAT0 is idx 23 and vice versa", metavar="invertVFATPos")
parser.add_option("--perchannel", action="store_true", dest="perchannel",
                  help="Run a per-channel sbit rate scan", metavar="perchannel")
parser.add_option("--time", type="int", dest="time", default = 3000,
                  help="Acquire time per point in milliseconds", metavar="time")
#parser.add_option("--zcc", action="store_true", dest="scanZCC",
#                  help="V3 Electronics only, scan the threshold on the ZCC instead of the ARM comparator", metavar="scanZCC")

parser.set_defaults(stepSize=2)
(options, args) = parser.parse_args()

remainder = (options.scanmax-options.scanmin+1) % options.stepSize
if remainder != 0:
    options.scanmax = options.scanmax - remainder
    print "Reducing scanmax to: ", options.scanmax

if options.scanmax > 255:
    print "CFG_THR_ARM_DAC and CFG_THR_ZCC_DAC only go up to 0xff (255)"
    print "Current value %i will roll over to 0"%(options.scanmax)
    print "Seting scanmax to 255"
    options.scanmax=255

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

    #Determine number of unmasked VFATs
    numUnmaskedVFATs=0
    for vfat in range(0,24):
        if (mask >> vfat) & 0x1: continue
        numUnmaskedVFATs+=1
    if options.perchannel:
        #determine total time in hours
        totalTime=(options.scanmax-options.scanmin)*(options.chMax-options.chMin)*numUnmaskedVFATs*(options.time/1000.)*(1./3600.)
        
        print("I see you've asked for a perchannel scan")
        print("Right now this is done in series, are you sure you want to continue?")
        print("I expect this will take: %f hours"%totalTime)
        
        bInputUnderstood=False
        performTest=raw_input("Do you want to continue? (yes/no)")
        while(not bInputUnderstood):
            performTest=performTest.upper()
            if performTest == "NO":
                print("Okay, exiting!")
                print("Please run again and change the '--vfatmask', '--chMin', '--chMax', '--scanmin', and/or '--scanmax' parameters")
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
    scanDataRatePerVFAT = (c_uint32 * (24 * scanDataSizeVFAT))()
    for vfat in range(0,24):
        if (mask >> vfat) & 0x1: continue

        #Make the OH Mask
        print("making OH mask for VFAT%i"%vfat)
        listMaskOh = list('0b'+'0'*24)
        if options.invertVFATPos:
            listMaskOh[2+vfat]='1'
        else:
            listMaskOh[2+(23-vfat)]='1'
        #print(''.join(listMaskOh))
        maskOh=(~(int(''.join(listMaskOh),2)) & 0xFFFFFF)
        print("maskOh =",hex(maskOh))

        #Set the OH VFAT_MASK to block sbits from every vfat except one
        #vfatBoard.parentOH.setSBitMask(maskOh) #Now done by the rpc module called by hwOptohybrid::performSBitRateScan(...)

        if options.perchannel:
            for chan in range(options.chMin,options.chMax+1):
                print("scanning %s of VFAT%i channel %i"%(scanReg, vfat, chan))

                # Perform the scan
                rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=maskOh, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT,
                                                                 dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, 
                                                                 chan=chan, scanReg=scanReg, time=options.time, invertVFATPos=options.invertVFATPos, isParallel=False)
        
                if rpcResp != 0:
                    print("sbit rate scan for VFAT%i channel %i failed"%(vfat,chan))
                    #raise Exception('RPC response was non-zero, sbit rate scan for VFAT%i failed'%vfat)
                    continue #For now just skip instead of crash
        
                #Store Output Data
                if options.debug:
                    print("VFAT\tChan\tDAC\tRate")
                for idx in range(0,scanDataSizeVFAT):
                    try:
                        Rate[0] = scanDataRate[idx]
                        vfatCH[0] = chan
                        vfatN[0] = vfat
                        vth[0] = scanDataDAC[idx]

                        if options.debug:
                            print("%i\t%i\t%i\t%i"%(vfat,chan,scanDataDAC[idx],scanDataRate[idx]))
                    except IndexError:
                        Rate[0] = -99
                        vfatCH[0]=128
                        vfatN[0] = vfat
                        vth[0] = options.scanmin+1+options.stepSize*idx
                        print("Unable to index data for VFAT%i idx %i expected DAC val"%(vfat, idx, vth[0]))
                    finally:
                        myT.Fill()

                myT.AutoSave("SaveSelf")
        else:
            print("scanning %s of VFAT%i for all channels"%(scanReg, vfat))
            
            # Perform the scan
            rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=maskOh, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT,
                                                             dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, 
                                                             scanReg=scanReg, time=options.time, invertVFATPos=options.invertVFATPos, isParallel=False)
        
            if rpcResp != 0:
                print("sbit rate scan for VFAT%i failed"%vfat)
                raise Exception('RPC response was non-zero, sbit rate scan for VFAT%i failed'%vfat)

            #Store Output Data
            if options.debug:
                print("VFAT\tDAC\tRate")
            for idx in range(0,scanDataSizeVFAT):
                try:
                    Rate[0] = scanDataRate[idx]
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = scanDataDAC[idx]

                    if options.debug:
                        print("%i\t%i\t%i"%(vfat,scanDataDAC[idx],scanDataRate[idx]))
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = options.scanmin+1+options.stepSize*idx
                    print("Unable to index data for VFAT%i idx %i expected DAC val"%(vfat, idx, vth[0]))
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
