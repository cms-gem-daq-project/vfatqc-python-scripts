#!/bin/env python
from ctypes import *
from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
from gempython.vfatqc.treeStructure import gemDacCalTreeStructure

import os
import ROOT as r

def getDACInfo():
    """
    Get minimum DAC value, maximum DAC value, and DAC name
    """

    print("You've requested a VFAT3 DAC Scan")
    printDACOptions()
    dacSelect=-1
    while(dacSelect not in maxVfat3DACSize.keys()):
        dacSelect=int(raw_input("Please select the dac number from the options above: "))
        if dacSelect not in maxVfat3DACSize.keys():
            print("Sorry input not understood") 

    retInfo = {
            "dacMax":maxVfat3DACSize[dacSelect][0],
            "dacMin":0,
            "dacName":maxVfat3DACSize[dacSelect][1],
            "dacSelect":dacSelect
            }

    return retInfo

def printDACOptions():
    print("dac\tName")
    print("===\t====")
    dacOptions = maxVfat3DACSize.keys()
    dacOptions.sort()
    for dacVal in dacOptions:
        print("%02d\t%s"%(dacVal,maxVfat3DACSize[dacVal][1]))
    return

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
    if args.dacSelect is None:
        dictDACInfo = getDACInfo()
        dacMax = dictDACInfo["dacMax"]
        dacMin = dictDACInfo["dacMin"]
        calTree.nameX[0] = dictDACInfo["dacName"]
        dacSelect = dictDACInfo["dacSelect"]
    else:
        dacMax = maxVfat3DACSize[args.dacSelect][0]
        dacMin = 0
        calTree.nameX[0] = maxVfat3DACSize[args.dacSelect][1]
        dacSelect = args.dacSelect

    # Get VFAT register values
    from gempython.utils.nesteddict import nesteddict as ndict
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)
    print("Getting CHIP IDs of all VFATs")
    vfatIDvals = ndict()
    irefVals = ndict()
    calSelPolVals = ndict()
    for ohN in range(0,12):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        # update the OH in question
        vfatBoard.parentOH.link = ohN

        # Get the cal sel polarity
        calSelPolVals[ohN] = vfatBoard.readAllVFATs("CFG_CAL_SEL_POL",ohVFATMaskArray[ohN])

        # Get the IREF values
        irefVals[ohN] = vfatBoard.readAllVFATs("CFG_IREF",ohVFATMaskArray[ohN])

        # Get the chip ID's
        vfatIDvals[ohN] = vfatBoard.getAllChipIDs(ohVFATMaskArray[ohN])

    # Perform DAC Scan
    arraySize = bin(args.ohMask).count("1") * (dacMax-dacMin+1)*24/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Performing DAC Scan on all links, this may take some time please be patient")
    rpcResp = amcBoard.performDacScanMultiLink(scanData,dacSelect,args.stepSize,args.ohMask,args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    #try:
    if args.debug:
        print("| link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :--: | :---: | :----: | :--: |:-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
    for dacWord in scanData:
        vfat = (dacWord >>18) & 0x1f
        ohN = ((dacWord >> 23) & 0xf)
        calTree.fill(
                calSelPol = calSelPolVals[ohN][vfat],
                dacSelect = dacSelect,
                dacValX = (dacWord & 0xff),
                dacValY = ((dacWord >> 8) & 0x3ff),
                dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                iref = irefVals[ohN][vfat],
                link = ohN,
                vfatID = vfatIDvals[ohN][vfat],
                vfatN = vfat
                )
        if args.debug:
            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} |".format(
                calTree.link[0],
                calTree.vfatN[0],
                str(hex(calTree.vfatID[0])).strip('L'),
                calTree.dacSelect[0],
                calTree.nameX[0],
                calTree.dacValX[0],
                calTree.dacValX_Err[0],
                calTree.nameY[0],
                calTree.dacValY[0],
                calTree.dacValY_Err[0]))
        pass
    #except Exception as error:
    #    print("Exception raised: {}".format(error))
    #    calTree.autoSave("SaveSelf")

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
    if args.dacSelect is None:
        dictDACInfo = getDACInfo()
        dacMax = dictDACInfo["dacMax"]
        dacMin = dictDACInfo["dacMin"]
        calTree.nameX[0] = dictDACInfo["dacName"]
        dacSelect = dictDACInfo["dacSelect"]
    else:
        dacMax = maxVfat3DACSize[args.dacSelect][0]
        dacMin = 0
        calTree.nameX[0] = maxVfat3DACSize[args.dacSelect][1]
        dacSelect = args.dacSelect
    
    # Determine VFAT mask
    if args.vfatmask is None:
        args.vfatmask = vfatBoard.parentOH.getVFATMask()
        if args.debug:
            print("Automatically determined vfatmask to be: {0}".format(str(hex(args.vfatmask)).strip('L')))
    
    # Get the cal sel polarity
    print("Getting Calibration Select Polarity of all VFATs")
    calSelPolVals = vfatBoard.readAllVFATs("CFG_CAL_SEL_POL",args.vfatmask)

    # Get the IREF values
    print("Getting IREF of all VFATs")
    irefVals = vfatBoard.readAllVFATs("CFG_IREF",args.vfatmask)

    # Determine Chip ID
    print("Getting CHIP IDs of all VFATs")
    vfatIDvals = vfatBoard.getAllChipIDs(args.vfatmask)
    
    # Perform DAC Scan
    arraySize = (dacMax-dacMin+1)*24/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Performing DAC Scan on Optohybrid {0}, this may take some time please be patient".format(vfatBoard.parentOH.link))
    rpcResp = vfatBoard.parentOH.performDacScan(scanData, dacSelect, args.stepSize, args.vfatmask, args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    # Store Data
    calTree.link[0] = vfatBoard.parentOH.link

    #try:
    if args.debug:
        print("| link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :--: | :---: | :----: | :--: | :-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
    for dacWord in scanData:
        vfat = (dacWord >>18) & 0x1f
        calTree.fill(
                calSelPol = calSelPolVals[vfat],
                dacSelect = dacSelect,
                dacValX = (dacWord & 0xff),
                dacValY = ((dacWord >> 8) & 0x3ff),
                dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                iref = irefVals[vfat],
                vfatID = vfatIDvals[vfat],
                vfatN = vfat
                )
        if args.debug:
            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} |".format(
                calTree.link[0],
                calTree.vfatN[0],
                str(hex(calTree.vfatID[0])).strip('L'),
                dacSelect,
                calTree.nameX[0],
                calTree.dacValX[0],
                calTree.dacValX_Err[0],
                calTree.nameY[0],
                calTree.dacValY[0],
                calTree.dacValY_Err[0]))
        pass
    #except Exception as error:
    #    print("Exception raised: {}".format(error))
    #    calTree.autoSave("SaveSelf")
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
    import argparse
    parser = argparse.ArgumentParser(description="Scans a given DAC on a VFAT3 against the chip's ADC.  Either the internally or externally referenced ADC can be used.  Scans all VFATs on a given link simultaneously")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'; if running on an AMC use 'local' instead", metavar="cardName")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    # Optional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            help = "Print additional debugging information")
    parser.add_argument("--dacSelect", type=int, dest="dacSelect",
            help = "DAC Selection", default=None)
    parser.add_argument("-e","--extRefADC", action="store_true", dest="extRefADC",
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

    if ((args.dacSelect not in maxVfat3DACSize.keys()) and (args.dacSelect is not None)):
        print("Input DAC selection {0} not understood".format(args.dacSelect))
        print("possible options include:")
        printDACOptions()
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
                    dacSelect=-1, #temporary value, will be over-ridden 
                    nameX="dummy", # temporary name, will be over-ridden
                    nameY=("ADC1" if args.extRefADC else "ADC0"),
                    description="GEM DAC Calibration of VFAT3 DAC"
            )

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

    outF.cd()
    calTree.autoSave("SaveSelf")
    calTree.write()
    outF.Close()

    print("All DAC Scans Completed. Goodbye")
