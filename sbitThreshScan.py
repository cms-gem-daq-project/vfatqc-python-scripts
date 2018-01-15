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
                  help="Run a per-channel VT1 scan", metavar="perchannel")
#parser.add_option("--zcc", action="store_true", dest="scanZCC",
#                  help="V3 Electronics only, scan the threshold on the ZCC instead of the ARM comparator", metavar="scanZCC")

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
Rate = array( 'i', [ 0 ] )
myT.Branch( 'Rate', Rate, 'Rate/I' )
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

    #Get VFAT Parameters

    #Perform Scan
    scanReg = "THR_ARM_DAC"
    scanDataSizeVFAT = (options.scanmax-options.scanmin+1)/options.stepSize
    scanDataDAC = (c_uint32 * scanDataSizeVFAT)()
    scanDataRate = (c_uint32 * scanDataSizeVFAT)()
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
        maskOh=hex(~(int(''.join(listMaskOh),2)) & 0xFFFFFF)
        print("maskOh =",hex(maskOh))

        #Set the OH VFAT_MASK to block sbits from every vfat except one
        vfatBoard.parentOH.setSBitMask(maskOh) 

        if options.perchannel:
            print("the --perchannel option is a placeholder for now")
        else:
            print("scanning %s of VFAT%i for all channels"%(scanReg, vfat))
            
            # Perform the scan
            rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=maskOh, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, 
                                                             dacMin=options.scanmin, dacMax=options.scanmax, stepSize=options.stepSize, scanReg=scanReg)
             
            if rpcResp != 0:
                print("sbit rate scan for VFAT%i failed"%vfat)
                #sys.exit(os.EX_SOFTWARE)
                raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

            #Store Output Data
            if options.debug:
                print("VFAT\tDAC\tRate")
            for idx in range(0,scanDataSizeVFAT):
                try:
                    Rate[0] = outDataTrigRate[idx]
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = outDataDacVal[idx]

                    if options.debug:
                        print("%i\t%i\t%i"%(vfat,outDataDacVal[idx],outDataTrigRate[idx]))
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = options.scanmin+1+options.stepSize*idx
                    print("Unable to index data for VFAT%i idx %i expected DAC val"%(vfat, idx, vth[0]))
                finally:
                    myT.Fill()
        myT.AutoSave("SaveSelf")

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
