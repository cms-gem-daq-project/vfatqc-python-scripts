#!/bin/env python
r"""
``run_Scans.py``
================

Synopsis
--------

**run_scans.py** [-**h**] [-**d**] [--**gemType** *GEMTYPE*] [--**detType** *DETTYPE*] {**dacScanV3**, **lat**, **monitorR**, **sbitMapNRate**, **sbitReadOut**, **sbitThres**, **scurve**, **thrDac**, **trim**}

Mandatory arguments
-------------------

.. program:: run_scans.py

Positional arguments
--------------------

.. option:: dacScanV3

    Uses the dacScanV3.py tool to perform a VFAT3 DAC scan on all unmasked optohybrids.

.. option:: lat

    Launches a latency scan using the ultraLatency.py tool

.. option:: monitorT

    Uses the monitorTemperatures.py tool to record temperature data to a file until a KeyboardInterrupt is used

.. option:: sbitMapNRate

    Uses the checkSbitMappingAndRate.py tool to investigate the sbit mapping and rate measurement in OH \& CTP7 FPGA

.. option:: sbitReadOut

    Uses the sbitReadOut.py tool to readout sbits

.. option:: sbitThresh

    Launches an sbit rate vs. CFG_THR_ARM_DAC scan using the sbitThreshScan.py tool

.. option:: scurve

    Launches an scurve scan using the ultraScurve.py tool

.. option:: thrDac

    Launches a threshold DAC scan using the ultraThreshold.py tool

.. option:: trim

    Launches a trim run using the trimChamber.py tool

Optional arguments
------------------

.. option:: -h, --help

    show the help message and exit

.. option:: -d, --debug

    Print debugging information

.. option:: --gemType <GEMTYPE>

    String defining the GEM variant, available options: [`'ge21'`, `'me0'`, `'ge11'`]

.. option:: --detType <DETTYPE>

    Detector type within gemType. If gemType is `'ge11'`, then this should be from the list [`'short'`, `'long'`]
    If gemType is `'ge21'`, this should be from the list [`'m1'`, `'m2'`, `'m3'`, `'m4'`, `'m5'`, `'m6'`, `'m7`', `'m8'`]
    If gemType is `'me0'`, this should be from the list `null`

Environment
-----------

The following `$SHELL` variables should be defined beforehand:

.. glossary::

:envvar: `BUILD_HOME`
    the location of your ``vfatqc-python-scripts`` directory
:envvar: `DATA_PATH`
    the location of input data

Then execute:

`source $BUILD_HOME/vfatqc-python-scripts/setup/paths.sh`
"""
from gempython.gemplotting.mapping.chamberInfo import chamber_config
from gempython.utils.wrappers import runCommand
from gempython.tools.amc_user_functions_xhal import *
from gempython.tools.hw_constants import gemVariants
from gempython.vfatqc.utils.qcutilities import getCardName
from gempython.vfatqc.utils.scanUtils import makeScanDir

import datetime
import os

def checkSbitMappingAndRate(args):
    """
    Launches a call of checkSbitMappingAndRate.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Checking SBIT Mapping for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "sbitMonInt", startTime, args.shelf)

        # Build Command
        cmd = [
                "checkSbitMappingAndRate.py",
                "--gemType={}".format(args.gemType),
                "--detType={}".format(args.detType),
                "--shelf={}".format(args.shelf),
                "--slot={}".format(args.slot),
                "-f {}/SBitMappingAndRateData.root".format(dirPath),
                "-g {}".format(ohN),
                "--nevts={}".format(args.nevts),
                "--rates={}".format(args.rates),
                "--time={}".format(args.time),
                "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
                "--voltageStepPulse"
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished Checking SBIT Mapping for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

    print("Finished Checking SBIT Mapping for all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def dacScanV3(args):
    """
    Launches a call of dacScanV3.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Make output directory
    dirPath = makeScanDir(args.slot, -1, "dacScanV3", startTime, args.shelf)

    # Build Command
    cmd = [
            "dacScanV3.py",
            "--gemType={}".format(args.gemType),
            "--detType={}".format(args.detType),
            "-f {}/dacScanV3.root".format(dirPath),
            str(args.shelf),
            str(args.slot),
            "0x{:x}".format(args.ohMask)
            ]

    # debug flag raised?
    if args.debug:
        cmd.insert(1,"--debug")

    # Additional Options
    if args.dacSelect is not None:
        cmd.insert(1,"--dacSelect={}".format(args.dacSelect))
    if args.extRefADC:
        cmd.insert(1,"--extRefADC")

    # Execute
    executeCmd(cmd,dirPath)
    print("Finished DAC scans for optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def executeCmd(cmd, dirPath):
    """
    Executes the command specified by cmd, writes a logfile to dirPath

    cmd - list which defines a command, see runCommand from gempython.utils.wrappers
    dirPath - physical filepath
    """

    from subprocess import CalledProcessError

    try:
        log = file("%s/scanLog.log"%(dirPath),"w")
        runCommand(cmd,log)
    except CalledProcessError as e:
        print("Caught exception: {0}".format(e))
    except Exception as e:
        print("Caught exception: {0}".format(e))
    finally:
        runCommand( ["chmod","-R","g+rw",dirPath] )
    return

def monitorT(args):
    """
    Launches a call of monitorTemperatures.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    dirPath = makeScanDir(args.slot, -1, "temperature", startTime, args.shelf)

    # Build Command
    cmd = [
            "monitorTemperatures.py",
            "--gemType={}".format(args.gemType),
            "--detType={}".format(args.detType),
            "-f {}/temperatureData.root".format(dirPath),
            "--noOHs",
            "--noVFATs",
            "-t {}".format(args.time),
            str(args.shelf),
            str(args.slot),
            "0x{:x}".format(args.ohMask)
            ]

    # debug flag raised?
    if args.debug:
        cmd.insert(1,"--debug")
    if args.extTempVFAT:
        cmd.insert(1,"--extTempVFAT")

    # Execute
    try:
        executeCmd(cmd,dirPath)
    except KeyboardInterrupt:
        print("Finished monitoring temperatures for optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def sbitReadOut(args):
    """
    Launches a call of sbitReadOut.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Reading out SBITs from shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "sbitMonRO", startTime, args.shelf)

        # Build Command
        cmd = [
                "sbitReadOut.py",
                "--gemType={}".format(args.gemType),
                "--detType={}".format(args.detType),
                "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
                str(args.shelf),
                str(args.slot),
                str(ohN),
                str(args.time),
                dirPath
                ]

        # debug flag raised?
        if args.debug:
            cmd.insert(1,"--debug")

        # Additional options
        if args.amc13local:
            cmd.insert(1,"--amc13local")
        if args.fakeTTC:
            cmd.insert(1,"--fakeTTC")
        if args.t3trig:
            cmd.insert(1,"--t3trig")

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished reading out SBITs from shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

    print("Finished reading out SBITs from all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def sbitThreshScan(args):
    """
    Launches a call of sbitThreshScan.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Make output directory
    dirPath = makeScanDir(args.slot, -1, "sbitRateor", startTime, args.shelf)

    # Build Command
    cmd = [
            "sbitThreshScan.py",
            "--gemType {}".format(args.gemType),
            "--detType {}".format(args.detType),
            "-f {}/SBitRateData.root".format(dirPath),
            "--scanmax={}".format(args.scanmax),
            "--scanmin={}".format(args.scanmin),
            "--stepSize={}".format(args.stepSize),
            "--waitTime={}".format(args.waitTime),
            str(args.shelf),
            str(args.slot),
            "0x{:x}".format(args.ohMask)
            ]

    # debug flag raised?
    if args.debug:
        cmd.insert(1,"--debug")

    # Execute
    executeCmd(cmd,dirPath)
    print("Finished all SBIT Rate vs. CFG_THR_ARM_DAC scans for all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def trimChamberV3(args):
    """
    Launches a call of trimChamberV3.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    # Get DATA_PATH
    dataPath = os.getenv("DATA_PATH")

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Trimming shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "trimV3", startTime, args.shelf)

        calDacCalFile = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[ohKey])
        calDacCalFileExists = os.path.isfile(calDacCalFile)
        if not calDacCalFileExists:
            print("Skipping shelf{0} slot{1} OH{2}, detector {3}, missing CFG_CAL_DAC Calibration file:\n\t{2}".format(
                args.shelf,
                args.slot,
                ohN,
                chamber_config[ohKey],
                calDacCalFile))
            continue

        # Get base command
        cmd = [
                "trimChamberV3.py",
                "--gemType {}".format(args.gemType),
                "--detType {}".format(args.detType),
                "--calFileCAL={}".format(calDacCalFile),
                "--chMax={}".format(args.chMax),
                "--chMin={}".format(args.chMin),
                "--dirPath={}".format(dirPath),
                "-g {}".format(ohN),
                "--latency={}".format(args.latency),
                "--mspl={}".format(args.mspl),
                "--nevts={}".format(args.nevts),
                "--shelf={}".format(args.shelf),
                "--slot={}".format(args.slot),
                "--trimPoints={}".format(args.trimPoints),
                "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
                "--voltageStepPulse"
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Additional optional arguments
        if args.armDAC is not None:
            cmd.append("--armDAC={}".format(args.armDAC))
        else:
            # Check to see if a vfatConfig exists
            vfatConfigFile = "{0}/configs/vfatConfig_{1}.txt".format(dataPath,chamber_config[ohKey])
            if os.path.isfile(vfatConfigFile):
                cmd.append("--vfatConfig={}".format(vfatConfigFile))
                pass
            pass

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished trimming shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

    print("Finished trimming all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def iterTrim(args):
    """
    Launches a call of iterativeTrim.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print("opened connection")

    # Get DATA_PATH
    dataPath = os.getenv("DATA_PATH")

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "iterTrim", startTime, args.shelf)

        calDacCalFile = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[ohKey])
        calDacCalFileExists = os.path.isfile(calDacCalFile)
        if not calDacCalFileExists:
            print("Skipping shelf{0} slot{1} OH{2}, detector {3}, missing CFG_CAL_DAC Calibration file:\n\t{2}".format(
                args.shelf,
                args.slot,
                ohN,
                chamber_config[ohKey],
                calDacCalFile))
            continue

    print("iterativeTrimming shelf{0} slot{1} 0x{2:x}".format(args.shelf,args.slot,args.ohMask,chamber_config[ohKey]))

    # Get base command
    cmd = [
        "iterativeTrim.py",
        "{}".format(args.shelf),
        "{}".format(args.slot),
        "0x{:x}".format(args.ohMask),
        "--chMax={}".format(args.chMax),
        "--chMin={}".format(args.chMin),
        "--latency={}".format(args.latency),
        "--maxIter={}".format(args.maxIter),
        "--nevts={}".format(args.nevts),
        "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
        "--sigmaOffset={}".format(args.sigmaOffset),
        "--highTrimCutoff={}".format(args.highTrimCutoff),
        "--highTrimWeight={}".format(args.highTrimWeight),
        "--highNoiseCut={}".format(args.highNoiseCut)
    ]

    # debug flag raised?
    if args.debug:
        cmd.append("-d")

    # add calFile flag
    if args.calFileCAL:
        cmd.append("--calFileCAL")

    # Additional optional arguments
    if args.armDAC is not None:
        cmd.append("--armDAC={}".format(args.armDAC))

    # add CPU usage flag
    if args.light:
        cmd.append("--light")
    if args.medium:
        cmd.append("--medium")
    if args.heavy:
        cmd.append("--heavy")

    # Execute
    executeCmd(cmd,dirPath)
    print("Finished iterativeTrimming on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def ultraLatency(args):
    """
    Launches a call of ultraLatency.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Launching CFG_LATENCY scan for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "latency", startTime, args.shelf)

        # Get base command
        cmd = [
                "ultraLatency.py",
                "--gemType={}".format(args.gemType),
                "--detType={}".format(args.detType),
                "--filename={}/LatencyScanData.root".format(dirPath),
                "-g {}".format(ohN),
                "--mspl={}".format(args.mspl),
                "--nevts={}".format(args.nevts),
                "--scanmax={}".format(args.scanmax),
                "--scanmin={}".format(args.scanmin),
                "--shelf={}".format(args.shelf),
                "--slot={}".format(args.slot),
                "--stepSize={}".format(args.stepSize),
                "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Additional options
        if args.throttle is not None:
            cmd.append( "--throttle=%i"%(args.throttle) )
        if args.amc13local:
            cmd.append( "--amc13local")
        if args.t3trig:
            cmd.append( "--t3trig")
        if args.randoms is not None:
            cmd.append( "--randoms=%i"%(args.randoms))
        if args.internal:
            cmd.append( "--internal")
            cmd.append( "--voltageStepPulse")
            if args.chan is not None:
                cmd.append("--chan={}".format(args.chan))
            if args.vcal is not None:
                cmd.append("--vcal={}".format(args.vcal))

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished CFG_LATENCY scan for shelf{0} slot{1} OH{2} detector {3}".format(args.slot,args.shelf,ohN,chamber_config[ohKey]))

    print("Finished all CFG_LATENCY scans for all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def ultraScurve(args):
    """
    Launches a call of ultraScurve.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    from gempython.vfatqc.utils.scanUtils import launchSCurve
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Launching scurve for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "scurve", startTime, args.shelf)
        logFile = "%s/scanLog.log"%(dirPath)

        # Launch the scurve
        launchSCurve(
                cardName = cardName,
                chMax = args.chMax,
                chMin = args.chMin,
                filename = "{}/SCurveData.root".format(dirPath),
                latency = args.latency,
                link = ohN,
                logFile = logFile,
                makeLogFile = True,
                mspl = args.mspl,
                nevts = args.nevts,
                setChanRegs = False,
                vfatmask = (args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN)),
                voltageStepPulse = True,
                gemType = args.gemType,
                detType = args.detType)

        # Execute
        runCommand( ["chmod","-R","g+r",dirPath] )
        print("Finished scurve for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

    print("Finished all scurves for all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

def ultraThreshold(args):
    """
    Launches a call of ultraThreshold.py

    args - object returned by argparse.ArgumentParser.parse_args()
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Determine number of OH's
    cardName = getCardName(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        ohKey = (args.shelf,args.slot,ohN)
        print("Launching CFG_THR_ARM_DAC scan for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

        # Get & make the output directory
        dirPath = makeScanDir(args.slot, ohN, "thresholdch", startTime, args.shelf)

        # Build Command
        cmd = [
                "ultraThreshold.py",
                "--gemType={}".format(args.gemType),
                "--detType={}".format(args.detType),
                "--chMax={}".format(args.chMax),
                "--chMin={}".format(args.chMin),
                "-f {0}/ThresholdScanData.root".format(dirPath),
                "-g {}".format(ohN),
                "--nevts={}".format(args.nevts),
                "--perchannel",
                "--shelf={}".format(args.shelf),
                "--slot={}".format(args.slot),
                "--vfatmask=0x{:x}".format(args.vfatmask if (args.vfatmask is not None) else amcBoard.getLinkVFATMask(ohN) ),
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished CFG_THR_ARM_DAC scan for shelf{0} slot{1} OH{2} detector {3}".format(args.shelf,args.slot,ohN,chamber_config[ohKey]))

    print("Finished all CFG_THR_ARM_DAC scans for all optohybrids on shelf{0} slot{1} in ohMask: 0x{2:x}".format(args.shelf,args.slot,args.ohMask))

    return

if __name__ == '__main__':
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt

    # create the parent parser for common options
    import argparse
    parent_parser = argparse.ArgumentParser(add_help = False)
    parent_parser.add_argument("shelf", type=int, help="uTCA crate shelf number")
    parent_parser.add_argument("slot", type=int, help="AMC slot number in the uTCA crate")
    parent_parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")

    # create the parser that sub parsers will come from
    parser = argparse.ArgumentParser(description='Arguments to supply to run_scans.py')

    # Option arguments shared by all commands
    parser.add_argument("-d","--debug", action="store_true",help = "Print additional debugging information")
    parser.add_argument("--gemType",type=str,help="String that defines the GEM variant, available from the list: {0}".format(gemVariants.keys()),default="ge11")
    parser.add_argument("--detType",type=str,help="Detector type within gemType. If gemType is 'ge11' then this should be from list {0}; if gemType is 'ge21' then this should be from list {1}; and if type is 'me0' then this should be from the list {2}".format(gemVariants['ge11'],gemVariants['ge21'],gemVariants['me0']),default=None)

    # Create sub parser
    subparserCmds = parser.add_subparsers(help="Available subcommands and their descriptions.  To view the sub menu call \033[92mrun_scans.py COMMAND -h\033[0m e.g. '\033[92mrun_scans.py dacScanV3 -h\033[0m'")

    # Create subparser for dacScanV3
    parser_dacScan = subparserCmds.add_parser("dacScanV3", help="Uses the dacScanV3.py tool to perform a VFAT3 DAC scan on all unmasked optohybrids", parents = [parent_parser])
    parser_dacScan.add_argument("--dacSelect",type=int,default=None,help="DAC Selection, see VFAT3 Manual")
    parser_dacScan.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")
    parser_dacScan.set_defaults(func=dacScanV3)

    # Create subparser for ultraLatency
    parser_latency = subparserCmds.add_parser("lat", help="Launches an latency using the ultraLatency.py tool", parents = [parent_parser])
    parser_latency.add_argument("--amc13local",action="store_true",help="Use AMC13 local trigger generator")
    parser_latency.add_argument("-c","--chan",type=int,default=None,help="Channel on VFATs to run the latency scan. Only applies when calling with --internal; otherwise OR of all channels is used.")
    parser_latency.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_latency.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_latency.add_argument("-i","--internal",action="store_true",help="Run scan using calibration module")
    parser_latency.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_latency.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_latency.add_argument("--randoms",type=int,default=None,help="Generate random triggers using AMC13 local trigger generator at rate specified")
    parser_latency.add_argument("--scanmin",type=int,default=0,help="Minimum CFG_LATENCY")
    parser_latency.add_argument("--scanmax",type=int,default=255,help="Maximum CFG_LATENCY")
    parser_latency.add_argument("--stepSize",type=int,default=1,help="Step size to use when scanning CFG_LATENCY")
    parser_latency.add_argument("--t3trig",action="store_true",help="Take L1A's from AMC13 T3 trigger input")
    parser_latency.add_argument("--throttle",type=int,default=None,help="factor by which to throttle the input L1A rate, e.g. new trig rate = L1A rate / throttle")
    parser_latency.add_argument("-v","--vcal",type=int,default=250,help="Height of CalPulse in DAC units for all VFATs")
    parser_latency.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_latency.set_defaults(func=ultraLatency)

    # Create subparser for monitorT
    parser_monT = subparserCmds.add_parser("monitorT", help="Uses the monitorTemperatures.py tool to record temperature data to a file until a KeyboardInterrupt is issued",parents = [parent_parser])
    parser_monT.add_argument("--extTempVFAT",action="store_true",help = "Use external PT100 sensors on VFAT3 hybrid; note only available in HV3b_V3 hybrids or later")
    parser_monT.add_argument("-t","--time",type=int,default=60,help="Time, in seconds, to wait in between readings")
    parser_monT.set_defaults(func=monitorT)

    # Create subparser for checkSbitMappingAndRate
    parser_sbitMapNRate = subparserCmds.add_parser("sbitMapNRate", help="Uses the checkSbitMappingAndRate.py tool to investigate the sbit mapping and rate measurement in OH & CTP7 FPGA", parents = [parent_parser])
    parser_sbitMapNRate.add_argument("-n","--nevts",type=int,default=100,help="Number of pulses for each channel")
    parser_sbitMapNRate.add_argument("-r","--rates",type=str,default="1e3,1e4,1e5,1e6,1e7",help="Comma separated list of floats that specifies the pulse rates to be considered")
    parser_sbitMapNRate.add_argument("-t","--time",type=int,default=1000,help="Acquire time per point in milliseconds")
    parser_sbitMapNRate.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_sbitMapNRate.set_defaults(func=checkSbitMappingAndRate)

    # Create subparser for sbitReadOut
    parser_sbitReadOut = subparserCmds.add_parser("sbitReadOut", help="Uses the sbitReadOut.py tool to readout sbits", parents = [parent_parser])
    parser_sbitReadOut.add_argument("time",type=int,help="time in seconds to acquire sbits for")

    parser_sbitReadOut.add_argument("--amc13local",action="store_true",help="Use AMC13 local trigger generator")
    parser_sbitReadOut.add_argument("--fakeTTC",action="store_true",help="Set up for using AMC13 local TTC generator")
    parser_sbitReadOut.add_argument("-s","--shelf",type=int,default=None,help="uTCA shelf cardName is located in")
    parser_sbitReadOut.add_argument("--t3trig",action="store_true",help="Take L1A's from AMC13 T3 trigger input")
    parser_sbitReadOut.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_sbitReadOut.set_defaults(func=sbitReadOut)

    # Create subparser for sbitThreshScan
    parser_sbitThresh = subparserCmds.add_parser("sbitThresh", help="Launches an sbit rate vs. CFG_THR_ARM_DAC scan using the sbitThreshScan.py tool", parents = [parent_parser])
    parser_sbitThresh.add_argument("--scanmin",type=int,default=0,help="Minimum CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("--scanmax",type=int,default=255,help="Maximum CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("--stepSize",type=int,default=1,help="Step size to use when scanning CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("--waitTime",type=int,default=1,help="Length of the time window within which the rate is measured, in seconds")
    parser_sbitThresh.set_defaults(func=sbitThreshScan)


    # Create subparser for ultraScurve
    parser_scurve = subparserCmds.add_parser("scurve", help="Launches an scurve using the ultraScurve.py tool",parents = [parent_parser])
    parser_scurve.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_scurve.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_scurve.add_argument("-l","--latency",type=int,default=33,help="Setting of CFG_LATENCY register")
    parser_scurve.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_scurve.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_scurve.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_scurve.set_defaults(func=ultraScurve)

    # Create subparser for ultraThreshold
    parser_threshold = subparserCmds.add_parser("thrDac", help="Launches an threshold using the ultraThreshold.py tool", parents = [parent_parser])
    parser_threshold.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_threshold.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_threshold.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_threshold.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_threshold.set_defaults(func=ultraThreshold)

    # Create subparser for trimChamberV3
    parser_trim = subparserCmds.add_parser("trim", help="Launches a trim run using the trimChamberV3.py tool", parents = [parent_parser])
    parser_trim.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_trim.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_trim.add_argument("-l","--latency",type=int,default=33,help="Setting of CFG_LATENCY register")
    parser_trim.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_trim.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_trim.add_argument("--trimPoints", type=str,default="-63,0,63",help="comma separated list of trim values to use in trimming, a set of scurves will be taken at each point")
    parser_trim.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_trim.add_argument("--armDAC",type=int,help="CFG_THR_ARM_DAC value to write to all VFATs. If not provided we will look under $DATA_PATH/configs for a vfatConfig_<DetectorName>.txt file where DetectorNames are from the chamber_config dictionary")

    #armDacGroup = parser_trim.add_mutually_exclusive_group()
    #armDacGroup.add_argument("--armDAC",type=int,help="CFG_THR_ARM_DAC value to write to all VFATs")
    #armDacGroup.add_argument("--vfatConfig",type=str,help="Specify file containing CFG_THR_ARM_DAC settings")

    parser_trim.set_defaults(func=trimChamberV3)

    # Create subparser for iterativeTrim
    parser_itertrim = subparserCmds.add_parser("itertrim", help="Launches a trim run using the iterativeTrim.py tool", parents = [parent_parser])
    parser_itertrim.add_argument("--calFileCAL", action="store_true", help="Get the calibration constants for CFG_CAL_DAC from calibration files in standard locations (DATA_PATH/DETECTOR_NAME/calFile_calDac_DETECTOR_NAME.txt); if not provided a DB query will be performed at runtime to extract this information based on VFAT ChipIDs", default=None)
    parser_itertrim.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_itertrim.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_itertrim.add_argument("-l","--latency",type=int,default=33,help="Setting of CFG_LATENCY register")
    parser_itertrim.add_argument("--maxIter", type=int, help="Maximum number of iterations to perform (e.g. number of scurves to take)", default=4)
    parser_itertrim.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_itertrim.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_itertrim.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are determined at runtime automatically.")
    parser_itertrim.add_argument("--armDAC",type=int,help="CFG_THR_ARM_DAC value to write to all VFATs. If not provided we will look under $DATA_PATH/configs for a vfatConfig_<DetectorName>.txt file where DetectorNames are from the chamber_config dictionary")

    from gempython.vfatqc.utils.scanInfo  import sigmaOffsetDefault, highTrimCutoffDefault, highTrimWeightDefault, highNoiseCutDefault

    parser_itertrim.add_argument("--sigmaOffset", type=float, help="Will align the mean + sigmaOffset*sigma", default=sigmaOffsetDefault)
    parser_itertrim.add_argument("--highTrimCutoff", type=int, help="Will weight channels that have a trim value above this (when set to 63, has no effect)", default=highTrimCutoffDefault)
    parser_itertrim.add_argument("--highTrimWeight", type=float, help="Will apply this weight to channels that have a trim value above the cutoff", default=highTrimWeightDefault)
    parser_itertrim.add_argument("--highNoiseCut", type=float, help="Threshold in fC for masking the channel due to high noise",default=highNoiseCutDefault)

    # Parser for specifying parallel analysis behavior
    # Need double percent signs, see: https://thomas-cokelaer.info/blog/2014/03/python-argparse-issues-with-the-help-argument-typeerror-o-format-a-number-is-required-not-dict/
    itertrim_cpu_group = parser_itertrim.add_mutually_exclusive_group(required=True)
    itertrim_cpu_group.add_argument("--light", action="store_true", help="Analysis uses only 25%% of available cores")
    itertrim_cpu_group.add_argument("--medium", action="store_true", help="Analysis uses only 50%% of available cores")
    itertrim_cpu_group.add_argument("--heavy", action="store_true", help="Analysis uses only 75%% of available cores")

    parser_itertrim.set_defaults(func=iterTrim)

    # Check env
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')

    from gempython.utils.gemlogger import getGEMLogger
    gemlogger = getGEMLogger(__name__)
    gemlogger.setLevel(logging.ERROR)

    import uhal
    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    # Parser the arguments and call the appropriate function
    args = parser.parse_args()
    args.func(args)

    print("Good-bye")
