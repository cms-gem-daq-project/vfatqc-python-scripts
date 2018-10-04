#!/bin/env python
from ctypes import *
from gempython.vfatqc.treeStructure import gemDacCalTreeStructure

import os
import ROOT as r

def getDACInfo():
    """
    Get minimum DAC value, maximum DAC value, and DAC name
    """

    from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
    print("You've requested a VFAT3 DAC Scan")
    print("dac\tName")
    print("===\t====")
    for dacVal,dacTuple in maxVfat3DACSize.iteritems():
        print("%02d\t%s"%(dacVal,dacTuple[1]))
    dacSelect=-1
    while(dacSelect not in maxVfat3DACSize.keys()):
        dacSelect=raw_input("Please select the dac number from the options above: ")
        if dacSelect not in maxVfat3DACSize.keys()):
            print("Sorry input not understood") 

    retInfo = {
            "dacMax":maxVfat3DACSize[dacSelect][0],
            "dacMin":0,
            "dacName":maxVfat3DACSize[dacSelect][1]
            }

    return retInfo

def scanAllLinks(args, calTree, vfatBoard):
    """
    Performs a DAC scan on all VFATs on all unmasked OH's on amcBoard

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instance of HwVFAT
    """

    # Get the AMC
    amcBoard = vfatBoard.parentOH.parentAMC

    # Get DAC value
    dictDACInfo = getDACInfo()
    dacMax = dictDACInfo["dacMax"]
    dacMin = dictDACInfo["dacMin"]
    dacName = dictDACInfo["dacName"]

    # Determine all Chip ID's
    from gempython.utils.nesteddict import nesteddict as ndict
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)
    print("Getting CHIP IDs of all VFATs")
    vfatIDvals = ndict()
    for ohN in range(0,12):
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
        vfatIDvals[ohN] = vfatBoard.getAllChipIDs(ohVFATMaskArray[ohN])

    # Perform DAC Scan
    arraySize = bin(args.ohMask).count("1") * (dacMax-dacMin+1)*24/args.dacStep
    scanData = (c_uint32 * arraySize)()
    print("Performing DAC Scan on all links, this may take some time please be patient")
    rpcResp = amcBoard.performDacScanMultiLink(scanData,args.dacSelect,args.dacStep,args.ohMask,args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    try:
        for dacWord in scanData:
            vfat = (dacWord >>18) & 0x1f
            calTree.fill(
                    dacValX = (dacWord & 0xff),
                    dacValY = ((dacWord >> 8) & 0x3ff),
                    dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                    link = ((dacWord >> 23) & 0xf),
                    vfatID = vfatIDvals[vfat],
                    vfatN = vfat
                    )
            pass
    except Exception as error:
        print("Exception raised: {}".format(error))
        calTree.autoSave("SaveSelf")
    #finally:
    #    calTree.write()

    print("DAC scans for optohybrids in {0} completed".format(args.ohMask))

    return

def scanSingleLink(args, calTree, vfatBoard):
    """
    Performs a DAC scan for the VFATs on the OH that vfatBoard.parentOH corresponds too

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instace of HwVFAT
    """

    # Get DAC value
    dictDACInfo = getDACInfo()
    dacMax = dictDACInfo["dacMax"]
    dacMin = dictDACInfo["dacMin"]
    dacName = dictDACInfo["dacName"]
    
    # Determine VFAT mask
    if args.vfatmask is None:
        args.vfatmask = vfatBoard.parentOH.getVFATMask()
        if args.debug:
            print("Automatically determined vfatmask to be: {0}".format(args.vfatmask))
    
    # Determine Chip ID
    print("Getting CHIP IDs of all VFATs")
    vfatIDvals = vfatBoard.getAllChipIDs(args.vfatmask)
    
    # Perform DAC Scan
    arraySize = (dacMax-dacMin+1)*24/args.dacStep
    scanData = (c_uint32 * arraySize)()
    print("Performing DAC Scan on Optohybrid {0}, this may take some time please be patient".format(vfatBoard.parentOH.link))
    rpcResp = vfatBoard.parentOH.performDacScan(scanData, dacSelect, args.dacStep, args.vfatmask, args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    # Store Data
    calTree.link = vfatBoard.parentOH.link

    try:
        for dacWord in scanData:
            vfat = (dacWord >>18) & 0x1f
            calTree.fill(
                    dacValX = (dacWord & 0xff),
                    dacValY = ((dacWord >> 8) & 0x3ff),
                    dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                    vfatID = vfatIDvals[vfat],
                    vfatN = vfat
                    )
            pass
    except Exception as error:
        print("Exception raised: {}".format(error))
        calTree.autoSave("SaveSelf")
    #finally:
    #    calTree.write()

    print("DAC scan for optohybrid {0} completed".format(vfatBoard.parentOH.link))

    return

if __name__ == '__main__':
    """
    Script to perform DAC scans with VFAT3
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    # create the parser
    from argparse
    parser = argparse.ArgumentParser(description="Scans a given DAC on a VFAT3 against the chip's ADC.  Either the internally or externally referenced ADC can be used.  Scans all VFATs on a given link simultaneously")

    # Positional arguments
    parser.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'; if running on an AMC use 'local' instead", metavar="cardName")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    # Optional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            help = "Print additional debugging information")
    paser.add_argument("-e","--extRefADC", action="store_true", dest="extRefADC",
            help = "Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-f","--filename",type=str,dest="filename",default="dacScanV3.root",
            help = "Specify output filename to store data in.")
    parser.add_argument("--series", action="store_true", dest="series",
            help = "Scan nonzero links in ohMask in series (successive RPC calls) instead of in parallel (one RPC call)")
    parser.add_argument("--stepSize", type=int, dest="stepSize",default=1, 
                  help="Supply a step size for the scan")
    parser.add_argument("-v","--vfatmask",type=parseInt,dest="vfatmask",default=None,
            help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFF masks all VFATs)")
    args = parser.parse_args()

    if args.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    # Open rpc connection to hw
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(args.cardName, 0, args.debug) # Assign link 0; we will update later
    print 'opened connection'
    amcBoard = vfatBoard.parentOH.parentAMC
    if amcBoard.fwVersion < 3:
        print("DAC Scan of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)
    
    # Check options
    from gempython.vfatqc.qcutilities import inputOptionsValid
    if not inputOptionsValid(args, amcBoard.fwVersion):
        exit(os.EX_USAGE)
        pass
    
    # Make output files
    outF = r.TFile(args.filename,"RECREATE")
    calTree = gemDacCalTreeStructure(
                    name="dacScanTree",
                    regX=dacName,
                    regY=("ADC1" if args.extRefADC else "ADC0"),
                    description="GEM DAC Calibration of DAC: {0}".format(dacName)
            )

    try:
        if args.series:
            for ohN in range(0, amcBoard.nOHs+1):
                if( not ((args.ohMask >> ohN) & 0x1)):
                    continue

                # update the OH in question
                vfatBoard.parentOH.link = ohN

                scanSingleLink(args, calTree, vfatBoard)
                pass
            pass
        else:
            scanAllLinks(args, calTree, vfatBoard)
            pass
    except Exception as error:
        print("Exception Raised: {}".format(error))
    finally:
        calTree.autoSave("SaveSelf")
        outF.cd()
        calTree.write()
        outF.Close()

    print("All DAC Scans Completed. Goodbye")
