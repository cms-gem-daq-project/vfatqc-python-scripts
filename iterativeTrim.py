#!/bin/env python
"""
Script to set trimdac values on a V3 chamber iteratively
By: Brian Dorney (brian.l.dorney@cern.ch)

Based on algorithmic description: https://indico.cern.ch/event/838248/contributions/3515801/attachments/1887448/3112771/VFAT3b_trim.pdf
"""

import os
import ROOT as r

from gempython.utils.gemlogger import printGreen, printYellow
from gempython.vfatqc.utils.qcutilities import getCardName

def iterativeTrim(args,dirPath,identifier, chanRegData=None, calInfo=None):
    """
    Takes an scurve at a given set of channel registers (all 0's if not provided) and
    returns a dictionary of numpy arrays with fit results (see gempythong.gemplotting.fitting.fitScanData
    for details on the output container).

    args        - Namespace produced by ArgumentParser.parse_args
    dirPath     - Output filepath location that scurve raw data should be saved at
    identifier  - Unique string identifier to be used for each iteration
    chanRegData - structure numpy array containing channel register data, expected dtype values are:
                  [('CALPULSE_ENABLE','bool'),('MASK','bool'),('ZCC_TRIM_POLARITY','bool'),
                  ('ZCC_TRIM_AMPLITUDE','uint8'),('ARM_TRIM_POLARITY','bool'),('ARM_TRIM_AMPLITUDE','uint8')].
                  If provided these values will be written to the channel registers of all unmaksed VFATs.
    calInfo     - Tuple of numpy arrays providing CFG_CAL_DAC calibration info, idx = 0 (1) for slopw (intercept)
                  indexed by VFAT position
    """

    from ctypes import *

    import root_numpy as rp

    from gempython.gemplotting.fitting.fitScanData import fitScanData
    #from gempython.gemplotting.utils.scurveAlgos import anaUltraScurve
    from gempython.vfatqc.utils.scanUtils import launchSCurve
    
    # Get Channel Register Info
    if chanRegData is None:
        setChanRegs = False
        cArray_trimVal = None
        cArray_trimPol = None
    else:
        setChanRegs = True
        cArray_trimVal = (c_uint32 * 3072)(*chanRegData["ARM_TRIM_AMPLITUDE"])
        cArray_trimPol = (c_uint32 * 3072)(*chanRegData["ARM_TRIM_POLARITY"])
        pass
    
    # Set filename of this scurve
    isZombie = True
    filename = "{:s}/SCurveData_{:s}.root".format(dirPath,identifier)
    if os.path.isfile(filename):
        scurveRawFile = r.TFile(filename,"READ")
        isZombie = scurveRawFile.IsZombie()

    # Check if scurve already exists, if not take one
    if not isZombie:
        try:
            thisTree = scurveRawFile.scurveTree
        except AttributeError as error:
            print("Caught exception {:s}".format(error))
            print("Going to re-take scurve corresponding to: {:s}".format(filename))
            launchSCurve(
                    calSF = args.calSF,
                    cardName = getCardName(args.shelf,args.slot),
                    chMax = args.chMax,
                    chMin = args.chMin,
                    debug = args.debug,
                    filename = filename,
                    latency = args.latency,
                    link = args.link,
                    mspl = args.pulseStretch,
                    nevts = args.nevts,
                    setChanRegs = setChanRegs,
                    trimARM = cArray_trimVal,
                    trimARMPol = cArray_trimPol,
                    vfatmask = args.vfatmask,
                    voltageStepPulse = not args.currentPulse)

            print("scurve finished")
    else:
        print("File {:s} either doesn't exist or is a zombie".format(filename))
        print("Going to re-take scurve corresponding to: {:s}".format(filename))
        launchSCurve(
                calSF = args.calSF,
                cardName = getCardName(args.shelf,args.slot),
                chMax = args.chMax,
                chMin = args.chMin,
                debug = args.debug,
                filename = filename,
                latency = args.latency,
                link = args.link,
                mspl = args.pulseStretch,
                nevts = args.nevts,
                setChanRegs = setChanRegs,
                trimARM = cArray_trimVal,
                trimARMPol = cArray_trimPol,
                vfatmask = args.vfatmask,
                voltageStepPulse = not args.currentPulse)

        print("scurve finished")
        pass

    print("Analyzing scurve {:s}".format(filename))
    return fitScanData(treeFileName=filename, isVFAT3=True, calTuple=calInfo)

# FIXME port this to gem-plotting-tools?
def writeChConfig(chConfig,vfat,vfatID,trimDAC,trimPol,mask,maskReason):
    """
    Writes the channel register information for VFAT position vfat

    chConfig - open file handle for writing data
    vfatID - VFAT Chip ID
    trimDAC - numpy array indexed by vfatCH containing ARM_TRIM_AMPLITUDE info
    trimPol - numpy array indexed by vfatCH containing ARM_TRIM_POLARITY info
    mask - numpy array indexed by vfatCH containing channel MASK bit
    maskReason - numpy array indexed by vfatCH containing mask reason word
    """

    # Couldn't figured out how to do this in the format I want with numpy...
    # Have to do it by hand
    for chan in range(0,128):
        chConfig.write('{:d}\t{:d}\t{:d}\t{:d}\t{:d}\t{:d}\t{:d}\n'.format(
                vfat,
                vfatID,
                chan,
                int(trimDAC[chan]),
                trimPol[chan],
                mask[chan],
                maskReason[chan]))
        pass # End loop over channels

    return

if __name__ == '__main__':
    import argparse
    import datetime
    import logging
    import sys

    import numpy as np
    import pandas as pd

    from gempython.gemplotting.utils.anautilities import parseCalFile
    from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
    from gempython.tools.vfat_user_functions_xhal import HwVFAT
    from gempython.utils.gemlogger import getGEMLogger
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.vfatqc.utils.confUtils import getChannelRegisters
    from gempython.vfatqc.utils.scanUtils import makeScanDir

    from reg_utils.reg_interface.common.reg_xml_parser import parseInt

    parent_parser = argparse.ArgumentParser(add_help = False)
    parent_parser.add_argument("shelf", type=int, help="uTCA crate shelf number")
    parent_parser.add_argument("slot", type=int, help="AMC slot number in the uTCA crate")
    parent_parser.add_argument("link", type=int, help="OH number on the AMC slot of interest")
    
    parser = argparse.ArgumentParser(description='Arguments to supply to iterativeTrim.py', parents = [parent_parser])
    parser.add_argument("--calFileCAL", type=str, help="File specifying calibration constants for CFG_CAL_DAC; if not provided a DB query will be performed at runtime to extract this information based on VFAT ChipIDs", default=None)
    parser.add_argument("--calSF", type=int, help="CFG_CAL_FS value to be used; no effect if --currentPulse is not supplied", default=0)
    parser.add_argument("--chMin", type=int, default = 0, help="Specify minimum channel number to scan")
    parser.add_argument("--chMax", type=int, default = 127, help="Specify maximum channel number to scan")
    parser.add_argument("-c","--currentPulse", action="store_true", help="Operate calibration mode in current pulse injection rather then voltage step pulse injection")
    parser.add_argument("--dirPath", type=str, default=None, help="Specify the path where the scan data should be stored")
    parser.add_argument("-d","--debug", action="store_true", help="Prints additional debugging information")
    parser.add_argument("-l","--latency", type=int, help="CFG_LATENCY value to be used",default=33)
    parser.add_argument("-m","--maxIter", type=int, help="Maximum number of iterations to perform (e.g. number of scurves to take)", default=4)
    parser.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser.add_argument("-p","--pulseStretch", type=int, help="CFG_PULSE_STRETCH value to be used",default=3)
    parser.add_argument("-v","--vfatmask",type=parseInt,default=0x0,help="Specifies which VFATs, if any, should be masked.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.")
    parser.add_argument("-z","--zeroChan",action="store_true",help="Zero all channel registers before beginning iterative trim procedure")

    args = parser.parse_args()

    # make scandir
    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.ERROR)
    if args.dirPath is not None:
        dirPath = args.dirPath
    else:
        startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
        dirPath = makeScanDir(args.slot, args.link, "trimV3", startTime, shelf=args.shelf)
        pass

    # Check to make sure dirPath exists
    if not os.path.exists(dirPath):
        print("Directory {:s} does not exist, exiting".format(dirPath))
        sys.exit(os.EX_CANTCREAT)

    # Declare the hardware board
    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName, args.link, args.debug)
    print("Opened connection")

    # Get all chip IDs
    vfatIDvals = vfatBoard.getAllChipIDs(args.vfatmask)

    # Get CFG_CAL_DAC calibration constants
    if args.calFileCAL is None:
        printYellow("Calibration info for CFG_CAL_DAC taken from DB query")
        dbInfo = getVFAT3CalInfo(vfatIDvals, debug=args.debug)
        tuple_calInfo = (dbInfo['cal_dacm'], dbInfo['cal_dacb'])
    else:
        printYellow("Calibration info for CFG_CAL_DAC taken from input file: {:s}".format(args.calFileCAL))
        tuple_calInfo = parseCalFile(args.calFileCAL)
        pass

    # Get initial channel registers
    if args.zeroChan:
        print("zero'ing all channel registers on (shelf{0}, slot{1}, OH{2})".format(args.shelf,args.slot,args.link))
        rpcResp = vfatBoard.setAllChannelRegisters(vfatMask=args.vfatmask)
                    
        if rpcResp != 0:
            raise Exception("{0}RPC response was non-zero, zero'ing all channel registers failed{1}".format(colors.RED,colors.ENDC))
        pass
    dataType=[
            ('CALPULSE_ENABLE','uint8'),
            ('MASK','uint8'),
            ('ZCC_TRIM_POLARITY','uint8'),
            ('ZCC_TRIM_AMPLITUDE','uint8'),
            ('ARM_TRIM_POLARITY','uint8'),
            ('ARM_TRIM_AMPLITUDE','uint8')]
    arrayInitChanReg = getChannelRegisters(vfatBoard, args.vfatmask)
    dict_chanRegArray = {}
    dict_chanRegArray[0] = arrayInitChanReg

    # Set a dummy mask reason since we are not using the full scurve analysis
    maskTransform = lambda x: (x & 0x1) << 5
    arrayMaskReason = np.array(map(maskTransform, arrayInitChanReg['MASK']))

    # Make containers for tracking iteration progress
    scurveStatTypes=[ ("iterN","uint8"),("vfatN","uint8"),("vfatID","uint32"),("avg","f4"),("std","f4"),("max","f4"),("min","f4"),("p2p","f4"),("n_trimmed","uint8") ]
    dfTrimResults = pd.DataFrame(np.zeros(0,dtype=scurveStatTypes ) )

    # Perform iterations
    for iterNum in range(1,args.maxIter+1):
        # Set iteration identifier
        identifier="iter{:d}".format(iterNum)

        # Take scurve and analyze results
        scurveFitResults = iterativeTrim(args,dirPath,identifier,chanRegData=dict_chanRegArray[iterNum-1], calInfo=tuple_calInfo)

        # Store chConfig info for this iteration
        chConfig = open("{:s}/chConfig_{:s}.txt".format(dirPath,identifier),"w")
        chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I:maskReason/I\n')

        # Define current channel register array container
        currentChanRegArray = np.zeros(3072, dtype=dataType)
        for entry in dataType:
            if ((entry[0] == "ARM_TRIM_POLARITY") or (entry[0] == "ARM_TRIM_AMPLITUDE")):
                continue
            currentChanRegArray[entry[0]]=dict_chanRegArray[iterNum-1][entry[0]]
            pass
        dict_chanRegArray[iterNum]=currentChanRegArray

        # Loop over VFATs
        maxSpread = -1 # maximum spread in scurve peak-2-peak
        for vfat in range(24):
            # Skip masked VFATs
            if (args.vfatmask >> vfat) & 0x1: 
                writeChConfig(chConfig,vfat,vfatIDvals[vfat],np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8))
                continue

            print("scurveFitResults[0][vfat] = {}".format(scurveFitResults[0][vfat]))
            print("len(scurveFitResults[0][vfat]) = {}".format(len(scurveFitResults[0][vfat])))

            # Determine scurve threshold statistics (do not include 0 values)
            scurveFitResultsNonzero = scurveFitResults[0][vfat][scurveFitResults[0][vfat]!=0]
            if (len(scurveFitResultsNonzero) > 0):
                avgScurveMean = np.mean(scurveFitResults[0][vfat][scurveFitResults[0][vfat]!=0])
                maxScurveMean = np.max(scurveFitResults[0][vfat][scurveFitResults[0][vfat]!=0])
                minScurveMean = np.min(scurveFitResults[0][vfat][scurveFitResults[0][vfat]!=0])
                stdScurveMean = np.std(scurveFitResults[0][vfat][scurveFitResults[0][vfat]!=0])
            else:
                printYellow("Warning: all scurve means are zoer for VFAT{} which is not in vfatmask 0x{:x}. Skipping".format(vfat,args.vfatmask))
                dict_chanRegArray[iterNum]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128] = dict_chanRegArray[iterNum-1]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128]
                dict_chanRegArray[iterNum]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128] = dict_chanRegArray[iterNum-1]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128]
                dfTrimResults = dfTrimResults.append(
                        {   "iterN":iterNum,
                            "vfatN":vfat,
                            "vfatID":vfatIDvals[vfat],
                            "avg":np.nan,
                            "std":np.nan,
                            "max":np.nan,
                            "min":np.nan,
                            "p2p":np.nan,
                            "n_trimmed":np.nan
                            },
                        ignore_index=True)
                writeChConfig(chConfig,vfat,vfatIDvals[vfat],np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8))
                continue

            # Update maxSpread?
            if (maxScurveMean - minScurveMean) > maxSpread:
                maxSpread = (maxScurveMean - minScurveMean)

            # See equation on step 3 of:
            # https://indico.cern.ch/event/838248/contributions/3515801/attachments/1887448/3112771/VFAT3b_trim.pdf
            trimDeltas = np.round(avgScurveMean - scurveFitResults[0][vfat]) * 15

            # Determine number of trimmed channels (e.g. trimDeltas == 0)
            uniqueVals, counts = np.unique(trimDeltas, return_counts=True)
            dict_trimValsByCounts = dict(zip(uniqueVals, counts))
            try:
                n_trimmed = dict_trimValsByCounts[0]
            except KeyError:
                n_trimmed = 0

            # Get the last trim DAC and Polarity values
            lastTrimPols = dict_chanRegArray[iterNum-1]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128]
            lastTrimDACs = dict_chanRegArray[iterNum-1]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128]
            
            # Apply the correct sign based on polarity to the last trim DAC values
            lastTrimDACs = np.multiply(pow(-1,lastTrimPols),lastTrimDACs)

            # Add trimDeltas to previous trimDACs
            currentTrimDACs = lastTrimDACs + trimDeltas

            # Determine polarity bit
            currentTrimPols = np.array( (currentTrimDACs < 0), dtype=np.uint8)

            if args.debug:
                pd.options.display.max_rows = 128
                dfTrimCalculation = pd.DataFrame()
                dfTrimCalculation['vfatCH'] = [x for x in range(128)]
                dfTrimCalculation['threshold'] = scurveFitResults[0][vfat]
                dfTrimCalculation['lastTrimDACs'] = lastTrimDACs
                dfTrimCalculation['lastTrimPols'] = lastTrimPols
                dfTrimCalculation['trimDeltas'] = trimDeltas
                dfTrimCalculation['currentTrimDACs'] = currentTrimDACs
                dfTrimCalculation['currentTrimPols'] = currentTrimPols
        
                printGreen("="*50+"VFAT{:d}: Iteration {:d}".format(vfat,iterNum)+"="*50)
                print("avgScurveMean = {}".format(avgScurveMean))
                print("cal_dacm = {}".format(tuple_calInfo[0][vfat]))
                print("cal_dacb = {}".format(tuple_calInfo[1][vfat]))
                print("n_trimmed = {}".format(n_trimmed))
                print(dfTrimCalculation)
                pass

            # Ensure no |trimDAC| is greater than 63
            currentTrimDACs = np.abs(currentTrimDACs)
            currentTrimDACs[currentTrimDACs > 63] = 63

            # Store this updated info
            dict_chanRegArray[iterNum]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128] = currentTrimPols
            dict_chanRegArray[iterNum]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128] = currentTrimDACs

            # Store statistics on scurve mean sample
            dfTrimResults = dfTrimResults.append(
                    {   "iterN":iterNum,
                        "vfatN":vfat,
                        "vfatID":vfatIDvals[vfat],
                        "avg":avgScurveMean,
                        "std":stdScurveMean,
                        "max":maxScurveMean,
                        "min":minScurveMean,
                        "p2p":maxScurveMean-minScurveMean,
                        "n_trimmed":n_trimmed
                        },
                    ignore_index=True)

            # Write this info to chConfig file
            writeChConfig(chConfig,vfat,vfatIDvals[vfat],currentTrimDACs,currentTrimPols,dict_chanRegArray[iterNum]["MASK"][vfat*128:(vfat+1)*128],arrayMaskReason[vfat*128:(vfat+1)*128])
            pass # end loop over VFATs

        chConfig.close()

        # Print a table that summarizes this iteration
        if args.debug:
            print(dfTrimResults[dfTrimResults["iterN"] == iterNum])

        # FIXME make some check on maximum spread in scurveMean values and if below tolerance, exit
        # Wait till we get to play with this on a few detectors before implementing
        pass

    printYellow("Table of peak-to-peak values of scurve mean positions by VFAT")
    print("="*100)
    for vfat in range(24):
        # Skip masked VFATs
        if (args.vfatmask >> vfat) & 0x1: 
            continue
        printGreen("="*50+"VFAT{:d}".format(vfat)+"="*50)
        print(dfTrimResults[dfTrimResults["vfatN"]==vfat][["iterN","vfatID","n_trimmed","avg","std","max","min","p2p"]])
        pass

    # Store iterative trim results
    dfTrimResults.to_csv(dirPath + "/iterativeTrimResults.csv",header=True,index=False)

    print("Trimming procedure completed")
