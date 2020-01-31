#!/bin/env python
"""
Script to set trimdac values on a V3 chamber iteratively
By: Brian Dorney (brian.l.dorney@cern.ch)

Based on algorithmic description: https://indico.cern.ch/event/838248/contributions/3515801/attachments/1887448/3112771/VFAT3b_trim.pdf
"""

import os
import ROOT as r

from gempython.utils.gemlogger import printGreen, printYellow, printRed
from gempython.vfatqc.utils.qcutilities import getCardName
from gempython.tools.amc_user_functions_xhal import HwAMC
from gempython.gemplotting.mapping.chamberInfo import chamber_config, GEBtype, CHANNELS_PER_VFAT
from gempython.tools.hw_constants import vfatsPerGemVariant

def iterativeTrim(args,dict_dirPaths,identifier,dict_chanRegData=None,dict_calFiles=None):
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

    from ctypes import c_uint32

    import root_numpy as rp

    from gempython.vfatqc.utils.scanUtils import launchSCurve

    dictOfFiles = {}

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue    

        ohKey = (args.shelf,args.slot,ohN)
        
        # Get Channel Register Info
        if dict_chanRegData is None:
            setChanRegs = False
            cArray_trimVal = None
            cArray_trimPol = None
        else:
            setChanRegs = True
            detName = chamber_config[ohKey]
            gemType = detName[:detName.find('-')].lower()
            cArray_trimVal = (c_uint32*vfatsPerGemVariant[gemType]*CHANNELS_PER_VFAT)(*dict_chanRegData[ohN]["ARM_TRIM_AMPLITUDE"])
            cArray_trimPol = (c_uint32*vfatsPerGemVariant[gemType]*CHANNELS_PER_VFAT)(*dict_chanRegData[ohN]["ARM_TRIM_POLARITY"])
            pass

        # Set filename of this scurve
        isZombie = True
        filename = "{:s}/SCurveData_{:s}.root".format(dict_dirPaths[ohN],identifier)
        dictOfFiles[ohKey] = (filename,chamber_config[ohKey],GEBtype[ohKey])
        if os.path.isfile(filename):
            scurveRawFile = r.TFile(filename,"READ")
            isZombie = scurveRawFile.IsZombie()
        
        # Take the scurves in sequence (it is not possible to take scurves in parallel)
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
                    link = ohN,
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
                link = ohN,
                mspl = args.pulseStretch,
                nevts = args.nevts,
                setChanRegs = setChanRegs,
                trimARM = cArray_trimVal,
                trimARMPol = cArray_trimPol,
                vfatmask = args.vfatmask,
                voltageStepPulse = not args.currentPulse)
            
            print("scurve finished")
            pass
        
    # Make the analysis output directories and set permissions
    from gempython.utils.wrappers import runCommand
    for scurveFile in dictOfFiles.values():
        runCommand(["mkdir", "-p", "{0}".format(scurveFile[0].replace(".root",""))])
        os.system("chmod -R g+rw {0} 2> /dev/null".format(scurveFile[0].replace(".root","")))
    
    # Do the analysis in parallel
    from multiprocessing import Pool
    from gempython.gemplotting.utils.anautilities import getNumCores2Use, init_worker
    pool = Pool(getNumCores2Use(args), initializer=init_worker) # Allocate number of CPU's based on getNumCores2Use()

    from gempython.gemplotting.utils.scurveAlgos import anaUltraScurveStar
    import itertools, sys, traceback

    try:
        print("Launching scurve analysis processes, this may take some time, please be patient")
        pool.map_async(anaUltraScurveStar,
            itertools.izip(
                [args for geoAddr in dictOfFiles.keys()],                                    # args namespace
                [scurveFile[0] for scurveFile in dictOfFiles.values()],                      # scurveFilename
                [dict_calFiles[geoAddr] for geoAddr in dictOfFiles.keys()],                  # calFile
                [scurveFile[2] for scurveFile in dictOfFiles.values()],                      # GEBtype
                [scurveFile[0].replace(".root","") for scurveFile in dictOfFiles.values()],  # outputDir
                [None for geoAddr in dictOfFiles.keys()]                                     # vfatList
                )
            ).get(7200) # wait at most 2 hours            
    except KeyboardInterrupt:
        printRed("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        raise Exception("Analysis failed.")        
    except Exception as err:
        printRed("Caught {0}: {1}, terminating workers".format(type(err), err.message))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        raise Exception("Analysis failed.")              
    except: # catch *all* exceptions
        e = sys.exc_info()[0]
        printRed("Caught non-Python Exception %s"%(e))
        pool.terminate()
        traceback.print_exc(file=sys.stdout)
        raise Exception("Analysis failed.")                      
    else:
        printGreen("Analysis Completed Successfully")
        pool.close()
        pool.join()

    scurveFitResults = {}    
        
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue    

        from gempython.gemplotting.utils.anaInfo import tree_names

        filename = "{0}/{1}".format(dict_dirPaths[ohN], tree_names["itertrimAna"][0].format(IDENTIFIER=identifier))

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile = r.TFile(filename,"READ")

        if not scanFile.IsOpen():
            raise IOError("iterativeTrim(): File {0} is not open or is not readable".format(filename))
        if scanFile.IsZombie():
            raise IOError("iterativeTrim(): File {0} is a zombie".format(filename))

        # Determine vfatID
        list_bNames = ['vfatN','vfatID']
        array_vfatData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)
        array_vfatData = np.unique(array_vfatData)

        # Get scurve data for this arm dac value (used for boxplots)
        list_bNames = ['vfatCH','vfatN','threshold', 'noise']
        scurveFitData = rp.tree2array(tree=scanFile.scurveFitTree, branches=list_bNames)
        
        scurveFitResults[ohN] = scurveFitData
        
    return scurveFitResults

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
    parent_parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered")
    
    parser = argparse.ArgumentParser(description='Arguments to supply to iterativeTrim.py', parents = [parent_parser])
    parser.add_argument("--calFileCAL", action="store_true", help="Get the calibration constants for CFG_CAL_DAC from calibration files in standard locations (DATA_PATH/DETECTOR_NAME/calFile_calDac_DETECTOR_NAME.txt); if not provided a DB query will be performed at runtime to extract this information based on VFAT ChipIDs", default=None)
    parser.add_argument("--calSF", type=int, help="CFG_CAL_FS value to be used; no effect if --currentPulse is not supplied", default=0)
    parser.add_argument("--chMin", type=int, default = 0, help="Specify minimum channel number to scan")
    parser.add_argument("--chMax", type=int, default = 127, help="Specify maximum channel number to scan")
    parser.add_argument("-c","--currentPulse", action="store_true", help="Operate calibration mode in current pulse injection rather then voltage step pulse injection")
    parser.add_argument("-d","--debug", action="store_true", help="Prints additional debugging information")
    parser.add_argument("-l","--latency", type=int, help="CFG_LATENCY value to be used",default=33)
    parser.add_argument("-m","--maxIter", type=int, help="Maximum number of iterations to perform (e.g. number of scurves to take)", default=4)

    from gempython.vfatqc.utils.scanInfo  import sigmaOffsetDefault, highTrimCutoffDefault, highTrimWeightDefault, highNoiseCutDefault
    
    parser.add_argument("--sigmaOffset", type=float, help="Will align the mean + sigmaOffset*sigma", default=sigmaOffsetDefault)
    parser.add_argument("--highTrimCutoff", type=int, help="Will weight channels that have a trim value above this (when set to 63, has no effect)", default=highTrimCutoffDefault)
    parser.add_argument("--highTrimWeight", type=float, help="Will apply this weight to channels that have a trim value above the cutoff", default=highTrimWeightDefault)    
    parser.add_argument("--highNoiseCut", type=float, help="Threshold in fC for masking the channel due to high noise", default=highNoiseCutDefault)
    
    parser.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser.add_argument("-p","--pulseStretch", type=int, help="CFG_PULSE_STRETCH value to be used",default=3)
    parser.add_argument("-v","--vfatmask",type=parseInt,default=0x0,help="Specifies which VFATs, if any, should be masked.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.")
    parser.add_argument("-z","--zeroChan",action="store_true",help="Zero all channel registers before beginning iterative trim procedure")
    parser.add_argument("--armDAC", type=int, default = None,help="CFG_THR_ARM_DAC value to write to all VFATs", metavar="armDAC")

    # Parser for specifying parallel analysis behavior
    # Need double percent signs, see: https://thomas-cokelaer.info/blog/2014/03/python-argparse-issues-with-the-help-argument-typeerror-o-format-a-number-is-required-not-dict/
    cpu_group = parser.add_mutually_exclusive_group(required=True)
    cpu_group.add_argument("--light", action="store_true", help="Analysis uses only 25%% of available cores")
    cpu_group.add_argument("--medium", action="store_true", help="Analysis uses only 50%% of available cores")
    cpu_group.add_argument("--heavy", action="store_true", help="Analysis uses only 75%% of available cores")    
    
    args = parser.parse_args()

    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.ERROR)
    
    dict_dirPaths = {}
    dict_calFiles = {}

    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print("Opened connection")
    
    # Get DATA_PATH
    dataPath = os.getenv("DATA_PATH")
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        dict_dirPaths[ohN] = makeScanDir(args.slot, ohN, "iterTrim", startTime, shelf=args.shelf)

        # Check to make sure dirPath exists
        if not os.path.exists(dict_dirPaths[ohN]):
            print("Directory {:s} does not exist, exiting".format(dict_dirPaths[ohN]))
            sys.exit(os.EX_CANTCREAT)

    # Declare the hardware board
    cardName = getCardName(args.shelf,args.slot)

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        vfatBoard = HwVFAT(cardName, ohN, args.debug)

        if args.armDAC is not None:
            vfatBoard.setVFATThresholdAll(mask=args.vfatmask, vt1=args.armDAC)
        else:
            ohKey = (args.shelf,args.slot,ohN)
            vfatConfigFile = "{0}/configs/vfatConfig_{1}.txt".format(dict_dirPaths[ohN],chamber_config[ohKey])

            if os.path.isfile(vfatConfigFile):
                print('Configuring VFAT Registers based on {0}'.format(args.vfatConfig))
                vfatTree = r.TTree('vfatTree','Tree holding VFAT Configuration Parameters')
                vfatTree.ReadFile(args.vfatConfig)
                
                for event in vfatTree:
                    # Skip masked vfats
                    if (args.vfatmask >> int(event.vfatN)) & 0x1:
                        continue
                    
                    # Write CFG_THR_ARM_DAC
                    print('Set link {0} VFAT{1} CFG_THR_ARM_DAC to {2}'.format(args.link,event.vfatN,event.vt1))
                    vfatBoard.setVFATThreshold(chip=int(event.vfatN), vt1=int(event.vt1))
                    
        # Get all chip IDs
        vfatIDvals = vfatBoard.getAllChipIDs(args.vfatmask)

        # Get CFG_CAL_DAC calibration constants
        if args.calFileCAL:
            calDacCalFile = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[ohKey])
            calDacCalFileExists = os.path.isfile(calDacCalFile)
            if not calDacCalFileExists:
                printRed("Missing CFG_CAL_DAC calibration file for shelf{0} slot{1} OH{2}, detector {3}:\n\t{4}".format(
                    args.shelf,
                    args.slot,
                    ohN,
                    chamber_config[ohKey],
                    calDacCalFile))
                raise Exception("Missing CFG_CAL_DAC Calibration file.")

            ohKey = (args.shelf,args.slot,ohN)            
            dict_calFiles[ohKey] = calDacCalFile
            pass
        
    # Get initial channel registers
    if args.zeroChan:
        print("zero'ing all channel registers on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))
        for ohN in range(0,amcBoard.nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue
            vfatBoard = HwVFAT(cardName, ohN, args.debug)
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

    dict_chanRegArray = {}
    dict_dfTrimResults = {}

    # Set a dummy mask reason since we are not using the full scurve analysis
    maskTransform = lambda x: (x & 0x1) << 5

    # Make containers for tracking iteration progress
    scurveStatTypes=[ ("iterN","uint8"),("vfatN","uint8"),("vfatID","uint32"),("avg","f4"),("std","f4"),("max","f4"),("min","f4"),("p2p","f4"),("n_trimmed","uint8") ]

    dict_chanRegArray = {}
    dict_chanRegArray[0] = {}
    
    #initialize bookkeeping information
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
        vfatBoard = HwVFAT(cardName, ohN, args.debug)
        arrayInitChanReg = getChannelRegisters(vfatBoard, args.vfatmask)

        dict_chanRegArray[0][ohN] = arrayInitChanReg

        dict_dfTrimResults[ohN] = pd.DataFrame(np.zeros(0,dtype=scurveStatTypes ) )

    # Perform iterations
    for iterNum in range(1,args.maxIter+1):
        # Set iteration identifier
        identifier="iter{:d}".format(iterNum)

        if args.calFileCAL:
            scurveFitResults = iterativeTrim(args,dict_dirPaths,identifier,dict_chanRegData=dict_chanRegArray[iterNum-1], dict_calFiles=dict_calFiles)
        else:
            scurveFitResults = iterativeTrim(args,dict_dirPaths,identifier,dict_chanRegData=dict_chanRegArray[iterNum-1], dict_calFiles=None)            

        dict_chanRegArray[iterNum]={}
        
        for ohN in range(0,amcBoard.nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            ohKey = (args.shelf,args.slot,ohN)
            
            # Store chConfig info for this iteration
            chConfig = open("{:s}/chConfig_{:s}.txt".format(dict_dirPaths[ohN],identifier),"w")
            chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I:maskReason/I\n')

            # Define current channel register array container
            detName = chamber_config[ohKey]
            gemType = detName[:detName.find('-')].lower()            
            currentChanRegArray = np.zeros(vfatsPerGemVariant[gemType]*CHANNELS_PER_VFAT, dtype=dataType)
            for entry in dataType:
                if ((entry[0] == "ARM_TRIM_POLARITY") or (entry[0] == "ARM_TRIM_AMPLITUDE")):
                    continue
                currentChanRegArray[entry[0]]=dict_chanRegArray[iterNum-1][ohN][entry[0]]
                pass
            dict_chanRegArray[iterNum][ohN]=currentChanRegArray

            # Loop over VFATs
            maxSpread = -1 # maximum spread in scurve peak-2-peak
            for vfat in range(24):
                # Skip masked VFATs
                if (args.vfatmask >> vfat) & 0x1: 
                    writeChConfig(chConfig,vfat,vfatIDvals[vfat],np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8),np.zeros(128,dtype=np.uint8))
                    continue

                # Get the last trim DAC and Polarity values
                print dict_chanRegArray[iterNum-1][ohN]
                lastTrimPols = dict_chanRegArray[iterNum-1][ohN]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128]
                lastTrimDACs = dict_chanRegArray[iterNum-1][ohN]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128]
            
                # Apply the correct sign based on polarity to the last trim DAC values
                lastTrimDACs = np.multiply(pow(-1,lastTrimPols),lastTrimDACs)

                toAlignValues = []
                toAlignWeights = []            
                channelMasks = []
                channelMaskReasons = []
            
                for ch in range(0,128):
                    if scurveFitResults[ohN][np.logical_and(scurveFitResults[ohN]["vfatN"] == vfat,scurveFitResults[ohN]["vfatCH"] == ch)]['noise'] > args.highNoiseCut:
                        channelMasks.append(1)
                        channelMaskReasons.append(0x08)
                        continue
                    else:
                        channelMasks.append(0)
                        channelMaskReasons.append(0)
                
                    if iterNum > 1 and lastTrimDACs[ch] > args.highTrimCutoff: 
                        toAlignValues.append(scurveFitResults[ohN][np.logical_and(scurveFitResults[ohN]["vfatN"] == vfat,scurveFitResults[ohN]["vfatCH"] == ch)]['threshold'] + args.sigmaOffset*scurveFitResults[ohN][np.logical_and(scurveFitResults[ohN]["vfatN"] == vfat,scurveFitResults[ohN]["vfatCH"] == ch)]['noise'])
                        toAlignWeights.append(args.highTrimWeight)
                    else:
                        toAlignValues.append(scurveFitResults[ohN][np.logical_and(scurveFitResults[ohN]["vfatN"] == vfat,scurveFitResults[ohN]["vfatCH"] == ch)]['threshold'] + args.sigmaOffset*scurveFitResults[ohN][np.logical_and(scurveFitResults[ohN]["vfatN"] == vfat,scurveFitResults[ohN]["vfatCH"] == ch)]['noise'])
                        toAlignWeights.append(1)

                if len(toAlignValues) > 0:
                    weightedSum=0.0
                    sumOfWeights=0.0
                    for i in range(len(toAlignValues)):
                        weightedSum+=toAlignValues[i]*toAlignWeights[i]
                        sumOfWeights+=toAlignWeights[i]

                    weightedMean = weightedSum/sumOfWeights    
                    
                    maxToAlignValues = np.max(toAlignValues)
                    minToAlignValues = np.min(toAlignValues)
                    stdToAlignValues = np.std(toAlignValues)
                    avgToAlignValues = np.mean(toAlignValues)                
                else:
                    printYellow("Warning: all scurve means are zoer for VFAT{} which is not in vfatmask 0x{:x}. Skipping".format(vfat,args.vfatmask))
                    dict_chanRegArray[iterNum][ohN]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128] = dict_chanRegArray[iterNum-1][ohN]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128]
                    dict_chanRegArray[iterNum][ohN]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128] = dict_chanRegArray[iterNum-1][ohN]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128]
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
                if (maxToAlignValues - minToAlignValues) > maxSpread:
                    maxSpread = (maxToAlignValues - minToAlignValues)

                # See equation on step 3 of:
                # https://indico.cern.ch/event/838248/contributions/3515801/attachments/1887448/3112771/VFAT3b_trim.pdf
                trimDeltas = np.round((weightedMean - (scurveFitResults[ohN][scurveFitResults[ohN]["vfatN"] == vfat]['threshold']+args.sigmaOffset*scurveFitResults[ohN][scurveFitResults[ohN]["vfatN"] == vfat]['noise'])) * 15)

                # Determine number of trimmed channels (e.g. trimDeltas == 0)
                uniqueVals, counts = np.unique(trimDeltas, return_counts=True)
                dict_trimValsByCounts = dict(zip(uniqueVals, counts))
                try:
                    n_trimmed = dict_trimValsByCounts[0]
                except KeyError:
                    n_trimmed = 0

                # Add trimDeltas to previous trimDACs
                currentTrimDACs = lastTrimDACs + trimDeltas

                # Determine polarity bit
                currentTrimPols = np.array( (currentTrimDACs < 0), dtype=np.uint8)

                if args.debug:
                    pd.options.display.max_rows = 128
                    dfTrimCalculation = pd.DataFrame()
                    dfTrimCalculation['vfatCH'] = [x for x in range(128)]
                    dfTrimCalculation['threshold'] = scurveFitResults[ohN][0][vfat]
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
                dict_chanRegArray[iterNum][ohN]["ARM_TRIM_POLARITY"][vfat*128:(vfat+1)*128] = currentTrimPols
                dict_chanRegArray[iterNum][ohN]["ARM_TRIM_AMPLITUDE"][vfat*128:(vfat+1)*128] = currentTrimDACs

                # Store statistics on scurve mean sample
                dict_dfTrimResults[ohN] = dict_dfTrimResults[ohN].append(
                    {   "iterN":iterNum,
                        "vfatN":vfat,
                        "vfatID":vfatIDvals[vfat],
                        "avg":avgToAlignValues,
                        "std":stdToAlignValues,
                        "max":maxToAlignValues,
                        "min":minToAlignValues,
                        "p2p":maxToAlignValues-minToAlignValues,
                        "n_trimmed":n_trimmed
                        },
                    ignore_index=True)

                # Write this info to chConfig file
                writeChConfig(chConfig,vfat,vfatIDvals[vfat],currentTrimDACs,currentTrimPols,channelMasks,channelMaskReasons)
                pass # end loop over VFATs

            chConfig.close()

            # Print a table that summarizes this iteration
            if args.debug:
                print(dfTrimResults[dfTrimResults["iterN"] == iterNum])


    printYellow("Table of peak-to-peak values of scurve mean positions by VFAT")                
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
                

        print("="*100)
        for vfat in range(24):
            # Skip masked VFATs
            if (args.vfatmask >> vfat) & 0x1: 
                continue
            printGreen("="*50+"VFAT{:d}".format(vfat)+"="*50)
            print(dict_dfTrimResults[ohN][dict_dfTrimResults[ohN]["vfatN"]==vfat][["iterN","vfatID","n_trimmed","avg","std","max","min","p2p"]])
            pass

        # Store iterative trim results
        dict_dfTrimResults[ohN].to_csv(dict_dirPaths[ohN] + "/iterativeTrimResults.csv",header=True,index=False)

    print("Trimming procedure completed")
