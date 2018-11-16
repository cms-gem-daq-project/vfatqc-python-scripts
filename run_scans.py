#!/bin/env python

from gempython.gemplotting.mapping.chamberInfo import chamber_config, chamber_vfatMask
from gempython.utils.wrappers import runCommand
from gempython.tools.amc_user_functions_xhal import *

import datetime
import os

def checkSbitMappingAndRate(args):
    """
    Launches a call of checkSbitMappingAndRate.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Checking SBIT Mapping for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "sbitMonInt", startTime)
        dirPath += "/{}".format(startTime)
        
        # Build Command
        cmd = [
                "checkSbitMappingAndRate.py",
                "--cardName={}".format(args.cardName),
                "-f {}/SBitMappingAndRateData.root".format(dirPath),
                "-g {}".format(ohN),
                "--nevts={}".format(args.nevts),
                "--rates={}".format(args.rates),
                "--time={}".format(args.time),
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L')),
                "--voltageStepPulse"
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")
        
        # Execute
        executeCmd(cmd,dirPath)
        print("Finished Checking SBIT Mapping for OH{0} detector {1}".format(ohN,chamber_config[ohN]))
    
    print("Finished Checking SBIT Mapping for all optohybrids in ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def dacScanV3(args):
    """
    Launches a call of dacScanV3.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Make output directory
    dirPath = makeScanDir(0, "dacScanV3", startTime)
    dirPath += "/{}".format(startTime)

    # Build Command
    cmd = [
            "dacScanV3.py",
            "-f {}/dacScanV3.root".format(dirPath),
            args.cardName,
            str(hex(args.ohMask)).strip('L')
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
    print("Finished DAC scans for optohybrids in ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

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
        runCommand( ["chmod","-R","g+r",dirPath] )
    return

def makeScanDir(ohN, scanType, startTime):
    """
    Makes a directory to store the output scan data and returns the directory path

    ohN - optohybrid number
    scanType - scanType, see ana_config.keys() from gempython.gemplotting.utils.anaInfo
    startTime - an instance of a datetime
    """

    from gempython.gemplotting.utils.anautilities import getDirByAnaType
    dirPath = getDirByAnaType(scanType, chamber_config[ohN])

    setupCmds = [] 
    setupCmds.append( ["mkdir","-p",dirPath+"/"+startTime] )
    setupCmds.append( ["chmod","g+rw",dirPath+"/"+startTime] )
    setupCmds.append( ["unlink",dirPath+"/current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"/current"] )
    for cmd in setupCmds:
        runCommand(cmd)

    return dirPath

def monitorT(args):
    """
    Launches a call of monitorTemperatures.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Make output directory
    #dirPath = "{}/temperature/".format(os.getenv("DATA_PATH"))
    #setupCmds = [] 
    #setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    #setupCmds.append( ["chmod","g+rw",dirPath+startTime] )
    #setupCmds.append( ["unlink",dirPath+"current"] )
    #setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    #for cmd in setupCmds:
    #    runCommand(cmd)
    dirPath = makeScanDir(0, "temperature", startTime)
    dirPath += "/{}".format(startTime)

    # Build Command
    cmd = [
            "monitorTemperatures.py",
            "-f {}/temperatureData.root".format(dirPath),
            "--noOHs",
            "--noVFATs",
            "-t {}".format(args.time),
            args.cardName,
            str(hex(args.ohMask)).strip('L')
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
        print("Finished monitoring temperatures for optohybrids in ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def sbitReadOut(args):
    """
    Launches a call of sbitReadOut.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Reading out SBITs from OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "sbitMonRO", startTime)
        dirPath += "/{}".format(startTime)
        
        # Build Command
        cmd = [
                "sbitReadOut.py",
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L')),
                args.cardName,
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
        if args.shelf is not None:
            cmd.insert(1,"--shelf={}".format(args.shelf))
        if args.t3trig:
            cmd.insert(1,"--t3trig")

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished reading out SBITs from OH{0} detector {1}".format(ohN,chamber_config[ohN]))
    
    print("Finished reading out SBITs from all optohybrids in ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def sbitThreshScan(args):
    """
    Launches a call of either sbitThreshScanSeries.py or sbitThreshScanParallel.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    tool="sbitThreshScanParallel.py"
    if args.series:
        tool="sbitThreshScanSeries.py"

    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Launching an SBIT Rate scan vs. CFG_THR_ARM_DAC for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "sbitRateor", startTime)
        dirPath += "/{}".format(startTime)
        
        # Build Command
        cmd = [
                tool,
                "--cardName={}".format(args.cardName),
                "-f {}/SBitRateData.root".format(dirPath),
                "-g {}".format(ohN),
                "--scanmax={}".format(args.scanmax),
                "--scanmin={}".format(args.scanmin),
                "--stepSize={}".format(args.stepSize),
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L'))
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Additional options
        if args.arm:
            cmd.append("--arm")
        if args.series:
            cmd.append("--time={}".format(args.time))

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished SBIT Rate scan vs. CFG_THR_ARM_DAC for OH{0} detector {1}".format(ohN,chamber_config[ohN]))
    
    print("Finished all SBIT Rate vs. CFG_THR_ARM_DAC scans for ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def trimChamberV3(args):
    """
    Launches a call of trimChamberV3.py
    
    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    # Get DATA_PATH
    dataPath = os.getenv("DATA_PATH")

    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Trimming OH{0} detector {1}".format(ohN,chamber_config[ohN]))
        
        # Get & make the output directory
        dirPath = makeScanDir(ohN, "trimV3", startTime)
        dirPath += "/{}".format(startTime)

        # Check to make sure calFiles exist
        armCalFile = "{0}/{1}/calFile_thrArmDAC_{1}.txt".format(dataPath,chamber_config[ohN])
        armCalFileExists = os.path.isfile(armCalFile)
        if not armCalFileExists:
            print("Skipping OH{0}, detector {1}, missing CFG_THR_ARM_DAC Calibration file:\n\t{2}".format(
                ohN,
                chamber_config[ohN],
                armCalFile))
            continue

        calDacCalFile = "{0}/{1}/calFile_calDac_{1}.txt".format(dataPath,chamber_config[ohN])
        calDacCalFileExists = os.path.isfile(calDacCalFile)
        if not calDacCalFileExists:
            print("Skipping OH{0}, detector {1}, missing CFG_CAL_DAC Calibration file:\n\t{2}".format(
                ohN,
                chamber_config[ohN],
                calDacCalFile))
            continue

        # Get base command
        cmd = [
                "trimChamberV3.py",
                "--cardName={}".format(args.cardName),
                "--calFileARM={}".format(armCalFile),
                "--calFileCAL={}".format(calDacCalFile),
                "--chMax={}".format(args.chMax),
                "--chMin={}".format(args.chMin),
                "--dirPath={}".format(dirPath),
                "-g {}".format(ohN),
                "--latency={}".format(args.latency),
                "--mspl={}".format(args.mspl),
                "--nevts={}".format(args.nevts),
                "--trimPoints={}".format(args.trimPoints),
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L')),
                "--voltageStepPulse"
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")
        
        # Additional optional arguments
        if args.armDAC is not None:
            cmd.append("--armDAC={}".format(args.armDAC))
        if args.vfatConfig is not None:
            cmd.append("--vfatConfig={}".format(args.vfatConfig))

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished trimming OH{0} detector {1}".format(ohN,chamber_config[ohN]))

    print("Finished trimming all optohybrids in ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def ultraLatency(args):
    """
    Launches a call of ultraLatency.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    cardName = "gem-shelf%02d-amc%02d"%(args.shelf,args.slot)
    amcBoard = HwAMC(cardName, args.debug)
    print('opened connection')

    from gempython.vfatqc.qcutilities import launchSCurve
    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Launching latency scan for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "latency", startTime)
        dirPath += "/{}".format(startTime)
        
        # Get base command
        cmd = [
                "ultraLatency.py",
                "--filename={}/LatencyScanData.root".format(dirPath),
                "-g {}".format(ohN),
                "--mspl={}".format(args.mspl),
                "--nevts={}".format(args.nevts),
                "--scanmax={}".format(args.scanmax),
                "--scanmin={}".format(args.scanmin),
                "--shelf={}".format(args.shelf),
                "--slot={}".format(args.slot),
                "--stepSize={}".format(args.stepSize),
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L'))
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
        print("Finished CFG_LATENCY scan for OH{0} detector {1}".format(ohN,chamber_config[ohN]))
    
    print("Finished all CFG_LATENCY scans for ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def ultraScurve(args):
    """
    Launches a call of ultraScurve.py

    args - object returned by argparse.ArgumentParser.parse_args() 
    """

    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    from gempython.vfatqc.qcutilities import launchSCurve
    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Launching scurve for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "scurve", startTime)
        dirPath += "/{}".format(startTime)
        logFile = "%s/scanLog.log"%(dirPath)

        # Launch the scurve
        launchSCurve(
                cardName = args.cardName,
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
                vfatmask = (args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN]),
                voltageStepPulse = True)

        # Execute
        runCommand( ["chmod","-R","g+r",dirPath] )
        print("Finished scurve for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

    print("Finished all scurves for ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

def ultraThreshold(args):
    """
    Launches a call of ultraThreshold.py
    
    args - object returned by argparse.ArgumentParser.parse_args() 
    """
    
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    
    # Determine number of OH's
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    for ohN in range(0,amcBoard.nOHs+1):
        # Skip masked OH's        
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
   
        print("Launching CFG_THR_ARM_DAC scan for OH{0} detector {1}".format(ohN,chamber_config[ohN]))

        # Get & make the output directory
        dirPath = makeScanDir(ohN, "thresholdch", startTime)
        dirPath += "/{}".format(startTime)
        
        # Build Command
        cmd = [
                "ultraThreshold.py",
                "--cardName={}".format(args.cardName),
                "--chMax={}".format(args.chMax),
                "--chMin={}".format(args.chMin),
                "-f {0}/ThresholdScanData.root".format(dirPath),
                "-g {}".format(ohN),
                "--nevts={}".format(args.nevts),
                "--perchannel",
                "--vfatmask={}".format(str(hex(args.vfatmask if (args.vfatmask is not None) else chamber_vfatMask[ohN])).strip('L'))
                ]

        # debug flag raised?
        if args.debug:
            cmd.append("-d")

        # Execute
        executeCmd(cmd,dirPath)
        print("Finished CFG_THR_ARM_DAC scan for OH{0} detector {1}".format(ohN,chamber_config[ohN]))
    
    print("Finished all CFG_THR_ARM_DAC scans for ohMask: {}".format(str(hex(args.ohMask)).strip('L')))

    return

if __name__ == '__main__':
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    
    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to run_scans.py')

    # Option arguments shared by all commands
    parser.add_argument("-d","--debug", action="store_true",help = "Print additional debugging information")

    # Create sub parser
    subparserCmds = parser.add_subparsers(help="Available subcommands and their descriptions.  To view the sub menu call \033[92mrun_scans.py COMMAND -h\033[0m e.g. '\033[92mrun_scans.py dacScanV3 -h\033[0m'")

    # Create subparser for dacScanV3
    parser_dacScan = subparserCmds.add_parser("dacScanV3", help="Uses the dacScanV3.py tool to perform a VFAT3 DAC scan on all unmasked optohybrids")

    parser_dacScan.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_dacScan.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")

    parser_dacScan.add_argument("--dacSelect",type=int,default=None,help="DAC Selection, see VFAT3 Manual")
    parser_dacScan.add_argument("-e","--extRefADC",action="store_true",help="Use the externally referenced ADC on the VFAT3.")

    parser_dacScan.set_defaults(func=dacScanV3)

    # Create subparser for ultraLatency
    parser_latency = subparserCmds.add_parser("lat", help="Launches an latency using the ultraLatency.py tool")
    
    parser_latency.add_argument("shelf",type=int, help="uTCA shelf number")
    parser_latency.add_argument("slot", type=int, help="slot in the uTCA of the AMC you are connecting too")
    parser_latency.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
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
    parser_latency.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    parser_latency.set_defaults(func=ultraLatency)
    
    # Create subparser for monitorT
    parser_monT = subparserCmds.add_parser("monitorT", help="Uses the monitorTemperatures.py tool to record temperature data to a file until a KeyboardInterrupt is issued")

    parser_monT.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_monT.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")

    parser_monT.add_argument("--extTempVFAT",action="store_true",help = "Use external PT100 sensors on VFAT3 hybrid; note only available in HV3b_V3 hybrids or later")
    parser_monT.add_argument("-t","--time",type=int,default=60,help="Time, in seconds, to wait in between readings")

    parser_monT.set_defaults(func=monitorT)

    # Create subparser for checkSbitMappingAndRate
    parser_sbitMapNRate = subparserCmds.add_parser("sbitMapNRate", help="Uses the checkSbitMappingAndRate.py tool to investigate the sbit mapping and rate measurement in OH & CTP7 FPGA")

    parser_sbitMapNRate.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_sbitMapNRate.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    parser_sbitMapNRate.add_argument("-n","--nevts",type=int,default=100,help="Number of pulses for each channel")
    parser_sbitMapNRate.add_argument("-r","--rates",type=str,default="1e3,1e4,1e5,1e6,1e7",help="Comma separated list of floats that specifies the pulse rates to be considered")
    parser_sbitMapNRate.add_argument("-t","--time",type=int,default=1000,help="Acquire time per point in milliseconds")
    parser_sbitMapNRate.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    parser_sbitMapNRate.set_defaults(func=checkSbitMappingAndRate)

    # Create subparser for sbitReadOut
    parser_sbitReadOut = subparserCmds.add_parser("sbitReadOut", help="Uses the sbitReadOut.py tool to readout sbits")
    
    parser_sbitReadOut.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_sbitReadOut.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    parser_sbitReadOut.add_argument("time",type=int,help="time in seconds to acquire sbits for")
    
    parser_sbitReadOut.add_argument("--amc13local",action="store_true",help="Use AMC13 local trigger generator")
    parser_sbitReadOut.add_argument("--fakeTTC",action="store_true",help="Set up for using AMC13 local TTC generator")
    parser_sbitReadOut.add_argument("-s","--shelf",type=int,default=None,help="uTCA shelf cardName is located in")
    parser_sbitReadOut.add_argument("--t3trig",action="store_true",help="Take L1A's from AMC13 T3 trigger input")
    parser_sbitReadOut.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")
    
    parser_sbitReadOut.set_defaults(func=sbitReadOut)
    
    # Create subparser for sbitThreshScanSeries
    parser_sbitThresh = subparserCmds.add_parser("sbitThresh", help="Launches an sbit rate vs. CFG_THR_ARM_DAC scan using the sbitThreshScanParallel.py tool")
    
    parser_sbitThresh.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_sbitThresh.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    parser_sbitThresh.add_argument("-a","--arm",action="store_true",help="Use only the arming comparator instead of the CFD")
    parser_sbitThresh.add_argument("--series",action="store_true",help="Use the sbitThreshScanSeries.py tool instead; note the scan will take much longer")
    parser_sbitThresh.add_argument("--scanmin",type=int,default=0,help="Minimum CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("--scanmax",type=int,default=255,help="Maximum CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("--stepSize",type=int,default=1,help="Step size to use when scanning CFG_THR_ARM_DAC")
    parser_sbitThresh.add_argument("-t","--time",type=int,default=1000,help="Acquire time per point in milliseconds")
    parser_sbitThresh.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    parser_sbitThresh.set_defaults(func=sbitThreshScan)


    # Create subparser for ultraScurve
    parser_scurve = subparserCmds.add_parser("scurve", help="Launches an scurve using the ultraScurve.py tool")
    
    parser_scurve.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_scurve.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    parser_scurve.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_scurve.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_scurve.add_argument("-l","--latency",type=int,default=33,help="Setting of CFG_LATENCY register")
    parser_scurve.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_scurve.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_scurve.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    parser_scurve.set_defaults(func=ultraScurve)

    # Create subparser for ultraThreshold
    parser_threshold = subparserCmds.add_parser("thrDac", help="Launches an threshold using the ultraThreshold.py tool")
    
    parser_threshold.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_threshold.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    parser_threshold.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_threshold.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_threshold.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_threshold.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    parser_threshold.set_defaults(func=ultraThreshold)
    
    # Create subparser for trimChamberV3
    parser_trim = subparserCmds.add_parser("trim", help="Launches a trim run using the trimChamberV3.py tool")
    
    parser_trim.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'")
    parser_trim.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    parser_trim.add_argument("--chMax",type=int,default=127,help="Specify maximum channel number to scan")
    parser_trim.add_argument("--chMin",type=int,default=0,help="Specify minimum channel number to scan")
    parser_trim.add_argument("-l","--latency",type=int,default=33,help="Setting of CFG_LATENCY register")
    parser_trim.add_argument("-m","--mspl",type=int,default=3,help="Setting of CFG_PULSE_STRETCH register")
    parser_trim.add_argument("-n","--nevts",type=int,default=100,help="Number of events for each scan position")
    parser_trim.add_argument("--trimPoints", type=str,default="-63,0,63",help="comma separated list of trim values to use in trimming, a set of scurves will be taken at each point")
    parser_trim.add_argument("--vfatmask",type=parseInt,default=None,help="If specified this will use this VFAT mask for all unmasked OH's in ohMask.  Here this is a 24 bit number, where a 1 in the N^th bit means ignore the N^th VFAT.  If this argument is not specified VFAT masks are taken from chamber_vfatMask of chamberInfo.py")

    armDacGroup = parser_trim.add_mutually_exclusive_group()
    armDacGroup.add_argument("--armDAC",type=int,help="CFG_THR_ARM_DAC value to write to all VFATs")
    armDacGroup.add_argument("--vfatConfig",type=str,help="Specify file containing CFG_THR_ARM_DAC settings")

    parser_trim.set_defaults(func=trimChamberV3)

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
