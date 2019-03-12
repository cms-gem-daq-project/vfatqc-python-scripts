#!/bin/env python

if __name__ == '__main__':
    """
    Script to measure sbit rate as a function of CFG_THR_ARM_DAC
    By: Brian Dorney (brian.l.dorney@cern.ch)
        Evaldas Juska (evaldas.juska@cern.ch)
    """
    
    import sys, os
    from array import array
    from ctypes import *
    
    from gempython.tools.vfat_user_functions_xhal import *
    
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="For each unmasked optohybrid this script will scan the CFG_THR_ARM_DAC register for each VFAT on the optohybrid. At each DAC point it will measure the rate of SBITs being sent to the optohybrid.  All links will be measured simultaneously.")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("shelf", type=int, help="uTCA shelf to access")
    parser.add_argument("slot", type=int,help="slot in the uTCA of the AMC you are connceting too")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    # Optional arguments
    parser.add_argument("--arm", action="store_true", dest="scanARM",
                      help="Use only the arming comparator instead of the CFD", metavar="scanARM")
    parser.add_argument("--chMin", type="int", dest = "chMin", default = 0,
                      help="Specify minimum channel number to scan", metavar="chMin")
    parser.add_argument("--chMax", type="int", dest = "chMax", default = 127,
                      help="Specify maximum channel number to scan", metavar="chMax")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug",
                      help="print extra debugging information", metavar="debug")
    parser.add_argument("-f", "--filename", type="string", dest="filename", default="SBitRateData.root",
                      help="Specify Output Filename", metavar="filename")
    parser.add_argument("--perchannel", action="store_true", dest="perchannel",
                      help="Run a per-channel sbit rate scan", metavar="perchannel")
    parser.add_argument("--scanmin", type="int", dest="scanmin",
                      help="Minimum value of scan parameter", metavar="scanmin", default=0)
    parser.add_argument("--scanmax", type="int", dest="scanmax",
                      help="Maximum value of scan parameter", metavar="scanmax", default=254)
    parser.add_argument("--stepSize", type="int", dest="stepSize", 
                      help="Supply a step size to the scan from scanmin to scanmax", metavar="stepSize", default=1)
    
    parser.set_defaults(stepSize=2)
    args = parser.parse_args()
    
    from gempython.utils.gemlogger import printRed, printYellow
    remainder = (args.scanmax-args.scanmin+1) % args.stepSize
    if remainder != 0:
        args.scanmax = args.scanmax - remainder
        printYellow("Reducing scanmax to: {0}".format(args.scanmax))
   
    if args.scanmax > 255:
        printYellow("CFG_THR_ARM_DAC and CFG_THR_ZCC_DAC only go up to 0xff (255)")
        printYellow("Current value %i will roll over to 0"%(args.scanmax))
        printYellow("Seting scanmax to 255")
        args.scanmax=255
    
    # Open rpc connection to hw
    from gempython.vfatqc.utils.qcutilities import getCardName, inputOptionsValid
    cardName = getCardName(args.shelf,args.slot)
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(cardName, 0, args.debug) # Assign link 0; we will update later
    print 'opened connection'
    amcBoard = vfatBoard.parentOH.parentAMC
    if amcBoard.fwVersion < 3:
        print("SBIT Threshold Scan of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)

    # Check options
    if not inputOptionsValid(args, amcBoard.fwVersion):
        exit(os.EX_USAGE)
        pass

    # Make output files
    import ROOT as r
    filename = args.filename
    myF = r.TFile(filename,'recreate')
    myT = r.TTree('rateTree','Tree Holding CMS GEM Sbit Rate Data')
    
    armDAC = array( 'i', [ 0 ] )
    myT.Branch( 'armDAC', armDAC, 'armDAC/I' )

    link = array( 'i', [ 0 ] )
    myT.Branch( 'link', link, 'link/I' )

    Rate = array( 'd', [ 0. ] )
    myT.Branch( 'Rate', Rate, 'Rate/D' )
    
    shelf = array( 'i', [ 0 ] )
    gemTree.Branch( 'shelf', self.shelf, 'shelf/I' )

    slot = array( 'i', [ 0 ] )
    gemTree.Branch( 'slot', self.slot, 'slot/I' )

    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
        
    vfatID = array( 'L', [0] )
    gemTree.Branch( 'vfatID', self.vfatID, 'vfatID/i' ) #Hex Chip ID of VFAT
    
    utime = array( 'i', [ 0 ] )
    myT.Branch( 'utime', utime, 'utime/I' )
    
    import datetime,time
    utime[0] = int(time.time())
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print startTime
    Date = startTime
    
    # Determine the per OH vfatmask
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)

    # Setup frontends before measurement
    for ohN in range(0, amcBoard.nOHs+1):
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
                
        # update the OH in question
        vfatBoard.parentOH.link = ohN
    
        #Place chips into run mode
        vfatBoard.setRunModeAll(ohVFATMaskArray[ohN], True, args.debug)
    
    #Store original CFG_SEL_COMP_MODE
    vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", mask)
    selCompVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
        range(0,24)))
    
    #Store original CFG_FORCE_EN_ZCC
    vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", mask)
    forceEnZCCVals_orig =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),
        range(0,24)))
    
    if args.scanARM: #Use arming comparator
        isCFD[0]=0
        vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE",0x1,mask)
        vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC",0x0,mask)
    else:               #Use CFD Mode (default)
        vfatBoard.writeAllVFATs("CFG_SEL_COMP_MODE",0x0,mask)
        vfatBoard.writeAllVFATs("CFG_FORCE_EN_ZCC",0x0,mask)
    
    #determine total time in hours
    if args.perchannel:
        totalTime=(args.scanmax-args.scanmin)*(args.chMax-args.chMin)*(1./3600.)
        
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
    scanDataSizeVFAT = (args.scanmax-args.scanmin+1)/args.stepSize
    scanDataDAC = (c_uint32 * scanDataSizeVFAT)()
    scanDataRate = (c_uint32 * scanDataSizeVFAT)()
    scanDataRatePerVFAT = (c_uint32 * (24 * scanDataSizeVFAT))()
    
    # Scan over all channels or just a channel OR???
    if args.perchannel:
        for chan in range(args.chMin,args.chMax+1):
            print("scanning %s for all VFATs channel %i"%(scanReg, chan))
    
            # Perform the scan
            rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=mask, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT, 
                                                             dacMin=args.scanmin, dacMax=args.scanmax, stepSize=args.stepSize, 
                                                             chan=chan, scanReg=scanReg, isParallel=True)
             
            if rpcResp != 0:
                print("sbit rate scan for all VFATs channel %i failed"%(chan))
                #raise Exception('RPC response was non-zero, sbit rate scan for VFAT%i failed'%vfat)
                continue #For now just skip instead of crash
    
            #Store Output Data - Per VFAT
            if args.debug:
                print("VFAT\tChan\tDAC\tRate")
            for vfat in range(0,24):
                for idx in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                    try:
                        Rate[0] = scanDataRatePerVFAT[idx]
                        vfatCH[0] = chan
                        vfatN[0] = vfat
                        vth[0] = scanDataDAC[idx-vfat*scanDataSizeVFAT]
    
                        if args.debug:
                            print("%i\t%i\t%i\t%i"%(vfat,chan,scanDataDAC[idx-vfat*scanDataSizeVFAT],scanDataRatePerVFAT[idx]))
                    except IndexError:
                        Rate[0] = -99
                        vfatCH[0]= chan
                        vfatN[0] = vfat
                        vth[0] = args.scanmin+1+args.stepSize*(idx-vfat*scanDataSizeVFAT)
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
                    vth[0] = args.scanmin+1+args.stepSize*(idx)
                finally:
                    myT.Fill()
    
            myT.AutoSave("SaveSelf")
    else:
        print("scanning %s for all VFATs channel OR"%(scanReg))
        
        # Perform the scan
        rpcResp = vfatBoard.parentOH.performSBitRateScan(maskOh=mask, outDataDacVal=scanDataDAC, outDataTrigRate=scanDataRate, outDataTrigRatePerVFAT=scanDataRatePerVFAT,
                                                         dacMin=args.scanmin, dacMax=args.scanmax, stepSize=args.stepSize, 
                                                         scanReg=scanReg, isParallel=True)
    
        if rpcResp != 0:
            print("sbit rate scan failed")
            raise Exception('RPC response was non-zero, sbit rate scan failed')
    
        # Store Output Data - Per VFAT
        if args.debug:
            print("VFAT\tidx\tDAC\tRate")
        for vfat in range(0,24):
            for idx in range(vfat*scanDataSizeVFAT,(vfat+1)*scanDataSizeVFAT):
                try:
                    Rate[0] = scanDataRatePerVFAT[idx]
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = scanDataDAC[idx-vfat*scanDataSizeVFAT]
    
                    if args.debug:
                        print("%i\t%i\t%i\t%i"%(vfat,idx,scanDataDAC[idx-vfat*scanDataSizeVFAT],scanDataRatePerVFAT[idx]))
                except IndexError:
                    Rate[0] = -99
                    vfatCH[0]=128
                    vfatN[0] = vfat
                    vth[0] = args.scanmin+1+args.stepSize*(idx-vfat*scanDataSizeVFAT)
                    print("Unable to index data for VFAT%i idx %i expected DAC val %i"%(vfat, idx, vth[0]))
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
                    vth[0] = args.scanmin+1+args.stepSize*(idx)
                    print("Unable to index data for Overall Case, idx %i expected DAC val %i"%(idx, vth[0]))
                finally:
                    myT.Fill()
        
        myT.AutoSave("SaveSelf")
    
    # Take chips out of run mode
    vfatBoard.setRunModeAll(mask, False, args.debug)
    
    # Return to original comparator settings
    for key,val in selCompVals_orig.iteritems():
        if (mask >> key) & 0x1: continue
        vfatBoard.writeVFAT(key,"CFG_SEL_COMP_MODE",val)
    for key,val in forceEnZCCVals_orig.iteritems():
        if (mask >> key) & 0x1: continue
        vfatBoard.writeVFAT(key,"CFG_FORCE_EN_ZCC",val)
