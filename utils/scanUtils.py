from ctypes import *

from gempython.gemplotting.mapping.chamberInfo import chamber_config
from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
from gempython.tools.vfat_user_functions_xhal import *
from gempython.utils.gemlogger import printGreen
from gempython.utils.wrappers import runCommand

def dacScanAllLinks(args, calTree, vfatBoard):
    """
    Performs a DAC scan on all VFATs on all unmasked OH's on amcBoard

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instance of HwVFAT
    """

    # Get the AMC
    amcBoard = vfatBoard.parentOH.parentAMC
    nVFATs = vfatBoard.parentOH.nVFATs

    # Get DAC value
    dacSelect = args.dacSelect
    dacMax = maxVfat3DACSize[dacSelect][0]
    dacMin = 0
    calTree.nameX[0] = maxVfat3DACSize[dacSelect][1]
    calTree.dacSelect[0] = dacSelect

    # Get VFAT register values
    from gempython.utils.nesteddict import nesteddict as ndict
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)
    print("Getting CHIP IDs of all VFATs")
    vfatIDvals = ndict()
    irefVals = ndict()
    calSelPolVals = ndict()
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            calSelPolVals[ohN] = [ 0 for vfat in range(0,nVFATs) ]
            irefVals[ohN] = [ 0 for vfat in range(0,nVFATs) ]
            vfatIDvals[ohN] = [ 0 for vfat in range(0,nVFATs) ]
        else:
            # update the OH in question
            vfatBoard.parentOH.link = ohN

            # Get the cal sel polarity
            calSelPolVals[ohN] = vfatBoard.readAllVFATs("CFG_CAL_SEL_POL",ohVFATMaskArray[ohN])

            # Get the IREF values
            irefVals[ohN] = vfatBoard.readAllVFATs("CFG_IREF",ohVFATMaskArray[ohN])

            # Get the chip ID's
            vfatIDvals[ohN] = vfatBoard.getAllChipIDs(ohVFATMaskArray[ohN])

    # Perform DAC Scan
    arraySize = amcBoard.nOHs * (dacMax-dacMin+1)*nVFATs/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Scanning DAC: {0} on all links".format(maxVfat3DACSize[dacSelect][1]))
    rpcResp = amcBoard.performDacScanMultiLink(scanData,dacSelect,args.stepSize,args.ohMask,args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred. DAC Scan of all links failed')

    #try:
    if args.debug:
        print("| detName | link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :-----: | :--: | :---: | :----: | :-------: |:-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
    for dacWord in scanData:
        # Get OH and skip if not in args.ohMask
        ohN  = ((dacWord >> 23) & 0xf)
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        # Get VFAT and skip if in ohVFATMaskArray[ohN]
        vfat = ((dacWord >> 18) & 0x1f)
        if ((ohVFATMaskArray[ohN] >> vfat) & 0x1):
            continue

        calTree.fill(
                calSelPol = calSelPolVals[ohN][vfat],
                dacValX = (dacWord & 0xff),
                dacValY = ((dacWord >> 8) & 0x3ff),
                dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                iref = irefVals[ohN][vfat],
                detName = chamber_config[(amcBoard.getShelf(),amcBoard.getSlot(),ohN)],
                link = ohN,
                shelf = amcBoard.getShelf(),
                slot = amcBoard.getSlot(),
                vfatID = vfatIDvals[ohN][vfat],
                vfatN = vfat
                )
        if args.debug:
            print("| {0} | {1} | {2} | 0x{3:x} | {4} | {5} | {6} | {7} | {8} | {9} | {10} |".format(
                calTree.detName[0],
                calTree.link[0],
                calTree.vfatN[0],
                calTree.vfatID[0],
                calTree.dacSelect[0],
                calTree.nameX[0],
                calTree.dacValX[0],
                calTree.dacValX_Err[0],
                calTree.nameY[0],
                calTree.dacValY[0],
                calTree.dacValY_Err[0]))
        pass

    printGreen("DAC scans for optohybrids in 0x{0:x} completed".format(args.ohMask))

    return

def dacScanSingleLink(args, calTree, vfatBoard):
    """
    Performs a DAC scan for the VFATs on the OH that vfatBoard.parentOH corresponds too

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instace of HwVFAT
    """

    # Get the AMC
    amcBoard = vfatBoard.parentOH.parentAMC

    nVFATs = vfatBoard.parentOH.nVFATs

    # Get DAC value
    dacSelect = args.dacSelect
    dacMax = maxVfat3DACSize[dacSelect][0]
    dacMin = 0
    calTree.nameX[0] = maxVfat3DACSize[dacSelect][1]
    calTree.dacSelect[0] = dacSelect,

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
    arraySize = (dacMax-dacMin+1)*nVFATs/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Scanning DAC {0} on Optohybrid {1}".format(maxVfat3DACSize[dacSelect][1], vfatBoard.parentOH.link))
    rpcResp = vfatBoard.parentOH.performDacScan(scanData, dacSelect, args.stepSize, args.vfatmask, args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred.  DAC Scan of OH{0} Failed'.format(vfatBoard.parentOH.link))

    # Store Data
    calTree.shelf[0]= amcBoard.getShelf()
    calTree.slot[0] = amcBoard.getSlot()
    calTree.link[0] = vfatBoard.parentOH.link

    #try:
    if args.debug:
        print("| detName | link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :-----: | :--: | :---: | :----: | :-------: | :-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
    for dacWord in scanData:
        vfat = (dacWord >>18) & 0x1f
        calTree.fill(
                calSelPol = calSelPolVals[vfat],
                dacValX = (dacWord & 0xff),
                dacValY = ((dacWord >> 8) & 0x3ff),
                dacValY_Err = 1, # convert to physical units in analysis, LSB is the error on Y
                iref = irefVals[vfat],
                vfatID = vfatIDvals[vfat],
                vfatN = vfat
                )
        if args.debug:
            print("| {0} | {1} | {2} | 0x{3:x} | {4} | {5} | {6} | {7} | {8} | {9} |".format(
                calTree.detName[0],
                calTree.link[0],
                calTree.vfatN[0],
                calTree.vfatID[0],
                calTree.dacSelect[0],
                calTree.nameX[0],
                calTree.dacValX[0],
                calTree.dacValX_Err[0],
                calTree.nameY[0],
                calTree.dacValY[0],
                calTree.dacValY_Err[0]))
        pass

    printGreen("DAC scan for optohybrid {0} completed".format(vfatBoard.parentOH.link))

    return

def launchSCurve(**kwargs):
    """
    Launches an scurve scan at a given set of trim settings

    Support arguments:
    calSF - int, value of the CFG_CAL_FS register
    cardName - string, name or ip address of AMC in uTCA crate
    chMask - array of ints, size 3072, indicates channels to mask; idx = vfatN * 128 + channel
    chMax - int, maximum channel
    chMin - int, minimum channel
    debug - boolean, print debugging information
    filename - string, physical filename indicating absolute path of scurve outputfile
    latency - int, latency to take the scruve at
    link - int, optohybrid number on cardName
    logFile - str, filepath to write the log file of the scurve call
    makeLogFile - bool, writes a log file of the scurve call, if logFile not provided defaults to /tmp/scurveLog_<time>.log
    mspl - int, value of MSPL or CFG_PULSE_STRETCH to use
    nevts - int, number of events to take in the scan
    setChanRegs - boolean, write VFAT channel registers if True
    vfatmask - int, vfatmask to use apply, 24-bit number, 1 in n^th bit indicates n^th vfat is masked
    voltageStepPulse - boolean, use voltage step pulse (true) instead of current pulse (false)
    trimARM - array of ints, size 3072, indicating trim amplitude to set for arming comparator; idx = vfatN * 128 + channel
    trimARMPol - as trimARM but sets trim polarity
    trimZCC - as trimARM but for the ZCC comparator
    trimZCCPol - as trimZCC but sets trim polarity
    gemType - gem generation (ge11, ge21 or me0)
    detType - gem detector type
    """

    import datetime
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")

    # Set defaults
    calSF = 0
    cardName = None
    chMask = None
    chMax = 127
    chMin = 0
    debug = False
    filename = None
    latency = 33
    link = 0
    logFile = "/tmp/scurveLog_{}.log".format(startTime)
    makeLogFile = False
    mspl = 3
    nevts = 100
    setChanRegs = False
    shelf = None
    slot = None
    vfatmask = 0x0
    voltageStepPulse = False
    trimARM = None
    trimARMPol = None
    trimZCC = None
    trimZCCPol = None
    gemType="ge11"
    detType="short"

    # Get defaults from kwargs
    from gempython.vfatqc.utils.qcutilities import getGeoInfoFromCardName
    if "calSF" in kwargs:
        calSF = kwargs["calSF"]
    if "cardName" in kwargs:
        cardName = kwargs["cardName"]
        geoInfo = getGeoInfoFromCardName(cardName)
        shelf = geoInfo["shelf"]
        slot = geoInfo["slot"]
    if "chMask" in kwargs:
        chMask = kwargs["chMask"]
    if "chMax" in kwargs:
        chMax = kwargs["chMax"]
    if "chMin" in kwargs:
        chMin = kwargs["chMin"]
    if "debug" in kwargs:
        debug = kwargs["debug"]
    if "filename" in kwargs:
        filename = kwargs["filename"]
    if "latency" in kwargs:
        latency = kwargs["latency"]
    if "link" in kwargs:
        link = kwargs["link"]
    if "logFile" in kwargs:
        logFile = kwargs["logFile"]
    if "makeLogFile" in kwargs:
        makeLogFile = kwargs["makeLogFile"]
    if "mspl" in kwargs:
        mspl = kwargs["mspl"]
    if "nevts" in kwargs:
        nevts = kwargs["nevts"]
    if "setChanRegs" in kwargs:
        setChanRegs = kwargs["setChanRegs"]
    if "shelf" in kwargs:
        shelf = kwargs["shelf"]
    if "slot" in kwargs:
        slot = kwargs["slot"]
    if "vfatmask" in kwargs:
        vfatmask = kwargs["vfatmask"]
    if "voltageStepPulse" in kwargs:
        voltageStepPulse = kwargs["voltageStepPulse"]
    if "trimARM" in kwargs:
        trimARM = kwargs["trimARM"]
    if "trimARMPol" in kwargs:
        trimARMPol = kwargs["trimARMPol"]
    if "trimZCC" in kwargs:
        trimZCC = kwargs["trimZCC"]
    if "trimZCCPol" in kwargs:
        trimZCCPol = kwargs["trimZCCPol"]
    if "gemType" in kwargs:
        gemType = kwargs["gemType"]
    if "detType" in kwargs:
        detType = kwargs["detType"]

    # Check minimum arguments
    import os
    if (not ((shelf is not None) and (slot is not None))):
        raise Exception("launchSCurve(): You must provide either an AMC network alias (e.g. 'eagle60'), an AMC ip address, or a geographic address (e.g. 'gem-shelf01-amc04')",os.EX_USAGE)
    if filename is None:
        raise Exception("launchSCurve(): You must provide a filename for this scurve. Exiting", os.EX_USAGE)

    # Set the channel registers
    if setChanRegs:
        if debug:
            print("opening an RPC connection to %s"%cardName)
        vfatBoard = HwVFAT(cardName, link, debug)

        if debug:
            print("setting channel registers")
        rpcResp = vfatBoard.setAllChannelRegisters(chMask=chMask, trimARM=trimARM, trimARMPol=trimARMPol, trimZCC=trimZCC, trimZCCPol=trimZCCPol, vfatMask=vfatmask, debug=debug)

        if rpcResp != 0:
            raise Exception("RPC response was non-zero, setting channel registers failed")

    # Make the command to be launched
    cmd = [ "ultraScurve.py",
            "--shelf=%i"%(shelf),
            "--slot=%i"%(slot),
            "-g%d"%(link),
            "--gemType=%s"%(gemType),
            "--detType=%s"%(detType),
            "--chMin=%i"%(chMin),
            "--chMax=%i"%(chMax),
            "--latency=%i"%(latency),
            "--mspl=%i"%(mspl),
            "--nevts=%i"%(nevts),
            "--vfatmask=0x%x"%(vfatmask),
            "--filename=%s"%(filename)
            ]
    if voltageStepPulse:
        cmd.append("--voltageStepPulse")
    else:
        cmd.append("--calSF=%i"%(calSF) )

    if debug:
        cmd.append("--debug")
        
    # launch the command
    if debug:
        print("launching an scurve with command:")
        command = ""
        for word in cmd:
            command = "%s %s"%(command, word)
        print(command)
    print("launching scurve for filename: %s"%filename)
    if makeLogFile:
        log = file(logFile,"w")
        runCommand(cmd,log)
    else:
        runCommand(cmd)

    return

def makeScanDir(slot, ohN, scanType, startTime, shelf=1, chamber_config=None):
    """
    Makes a directory to store the output scan data and returns the directory path

    ohN - optohybrid number
    scanType - scanType, see ana_config.keys() from gempython.gemplotting.utils.anaInfo
    startTime - an instance of a datetime
    shelf - uTCA shelf number
    chamber_config - chamber_config dictionary
    """

    ohKey = (shelf,slot,ohN)

    if chamber_config is None:
        from gempython.gemplotting.mapping.chamberInfo import chamber_config
    from gempython.gemplotting.utils.anautilities import getDirByAnaType
    if ohKey in chamber_config.keys():
        dirPath = getDirByAnaType(scanType, chamber_config[ohKey])
    else:
        dirPath = getDirByAnaType(scanType, "")

    setupCmds = []
    setupCmds.append( ["mkdir","-p",dirPath+"/"+startTime] )
    setupCmds.append( ["chmod","g+rw",dirPath+"/"+startTime] )
    setupCmds.append( ["unlink",dirPath+"/current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"/current"] )
    for cmd in setupCmds:
        runCommand(cmd)

    return "{:s}/{:s}".format(dirPath,startTime)

def sbitRateScanAllLinks(args, rateTree, vfatBoard, chan=128, scanReg="CFG_THR_ARM_DAC"):
    """
    Measures the rate of sbits from all VFATs on all unmasked optohybrids against an arbitrary register

    args - parsed arguments from an ArgumentParser instance
    rateTree - instance of gemSbitRateTreeStructure
    vfatBoard - instance of HwVFAT
    chan - VFAT channel to be scanned, if 128 is supplied the OR of all channels will be taken
    scanReg - Name of the VFAT register to scan against
    """

    # Check to make sure required parameters exist, if not provide a default
    if hasattr(args, 'debug') is False: # debug
        args.debug = False
    if hasattr(args, 'ohMask') is False: # ohMask
        args.ohMask = 0xfff
    if hasattr(args, 'perchannel') is False: # Channel scan?
        args.perchannel = False
    if hasattr(args, 'scanmax') is False: # scanmax
        args.scanmax = 255
    if hasattr(args, 'scanmin') is False: # scanmin
        args.scanmin = 0
    if hasattr(args, 'stepSize') is False: # stepSize
        args.stepSize = 0

    # Remove the leading "CFG_" since this is not expected by the RPC module
    if "CFG_" in scanReg:
        scanReg = scanReg.replace("CFG_","")
        pass

    # Get the AMC
    amcBoard = vfatBoard.parentOH.parentAMC

    # Determine the per OH vfatmask
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)
    if args.debug:
        for ohN in range(0,amcBoard.nOHs):
            # Skip masked OH's
            if( not ((args.ohMask >> ohN) & 0x1)):
                continue

            print("vfatMask for OH{0} is 0x{1:x}".format(ohN,ohVFATMaskArray[ohN]))
            pass
        pass

    #print("Getting CHIP IDs of all VFATs")
    vfatIDvals = {}
    selCompVals_orig = {}
    forceEnZCCVals_orig = {}
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        # update the OH in question
        vfatBoard.parentOH.link = ohN

        # Get the chip ID's
        vfatIDvals[ohN] = vfatBoard.getAllChipIDs(ohVFATMaskArray[ohN])

        #Place chips into run mode
        vfatBoard.setRunModeAll(ohVFATMaskArray[ohN], True, args.debug)

        #Store original CFG_SEL_COMP_MODE
        vals  = vfatBoard.readAllVFATs("CFG_SEL_COMP_MODE", ohVFATMaskArray[ohN])
        selCompVals_orig[ohN] =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))

        #Store original CFG_FORCE_EN_ZCC
        vals = vfatBoard.readAllVFATs("CFG_FORCE_EN_ZCC", ohVFATMaskArray[ohN])
        forceEnZCCVals_orig[ohN] =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))
        pass

    # Make the containers
    nDACValues = (args.scanmax-args.scanmin+1)/args.stepSize
    arraySize = 12 * nDACValues
    scanDataDAC = (c_uint32 * arraySize)()
    scanDataRate = (c_uint32 * arraySize)()
    scanDataRatePerVFAT = (c_uint32 * (24 * arraySize))() # per VFAT

    # Perform SBIT Rate Scan vs. scanReg
    if chan==128:
        strChannels="(OR of all channels per VFAT)"
    else:
        strChannels="(only from channel {0} for each VFAT)".format(chan)
        pass
    print("scanning {0} for all VFATs in ohMask 0x{1:x} {2}".format(scanReg,args.ohMask,strChannels))
    rpcResp = amcBoard.performSBITRateScanMultiLink(
            scanDataDAC,
            scanDataRate, #this is actually a rate i.e. it has units of Hz
            scanDataRatePerVFAT, #this is actually not a rate - it is an integrated count
            chan=chan,
            dacMin=args.scanmin,
            dacMax=args.scanmax,
            dacStep=args.stepSize,
            ohMask=args.ohMask,
            scanReg=scanReg,
            waitTime=args.waitTime)

    if rpcResp != 0:
        raise Exception('RPC response was non-zero, sbit rate scan failed')

    # place holder
    if args.debug:
        print("| detName | link | vfatN | vfatID | vfatCH | nameX | dacValX | rate |")
        print("| :-----: | :--: | :---: | :----: | :----: | :---: | :-----: | :--: |")
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        # Fill per VFAT rate
        for vfat in range(0,24):
            # Skip masked VFATs
            if ((ohVFATMaskArray[ohN] >> vfat) & 0x1):
                continue

            for dacVal in range(args.scanmin,args.scanmax+1,args.stepSize):
                idxVFAT = ohN*24*nDACValues + vfat*nDACValues+(dacVal-args.scanmin)/args.stepSize;
                idxDAC = ohN*nDACValues + (dacVal-args.scanmin)/args.stepSize
                rateTree.fill(
                        dacValX = scanDataDAC[idxDAC],
                        detName = chamber_config[(amcBoard.getShelf(),amcBoard.getSlot(),ohN)],
                        link = ohN,
                        nameX = scanReg,
                        #as mentioned above, scanDataRatePerVFAT is actually a count, unlike scanDateRate which is already a rate
                        rate = scanDataRatePerVFAT[idxVFAT]/float(args.waitTime),
                        shelf = amcBoard.getShelf(),
                        slot = amcBoard.getSlot(),
                        vfatCH = chan,
                        vfatID = vfatIDvals[ohN][vfat],
                        vfatN = vfat
                        )
                if args.debug:
                    print("| {0} | {1} | {2} | 0x{3:x} | {4} | {5} | {6} | {7} |".format(
                            rateTree.detName[0],
                            rateTree.link[0],
                            rateTree.vfatN[0],
                            rateTree.vfatID[0],
                            rateTree.vfatCH[0],
                            rateTree.nameX[0],
                            rateTree.dacValX[0],
                            rateTree.rate[0]
                            )
                        )
                    pass
                pass
            pass

        # Fill overall rate
        for dacVal in range(args.scanmin,args.scanmax+1,args.stepSize):
            idxDAC = ohN*nDACValues + (dacVal-args.scanmin)/args.stepSize
            rateTree.fill(
                    dacValX = scanDataDAC[idxDAC],
                    detName = chamber_config[(amcBoard.getShelf(),amcBoard.getSlot(),ohN)],
                    link = ohN,
                    nameX = scanReg,
                    #as mentioned above, scanDataRate is already a rate, unlike scanDataRatePerVFAT which is actually a count
                    rate = scanDataRate[idxDAC],
                    shelf = amcBoard.getShelf(),
                    slot = amcBoard.getSlot(),
                    vfatCH = chan,
                    vfatID = 0xdead,
                    vfatN = 24
                    )
            if args.debug:
                print("| {0} | {1} | {2} | 0x{3:x} | {4} | {5} | {6} | {7} |".format(
                        rateTree.detName[0],
                        rateTree.link[0],
                        rateTree.vfatN[0],
                        rateTree.vfatID[0],
                        rateTree.vfatCH[0],
                        rateTree.nameX[0],
                        rateTree.dacValX[0],
                        rateTree.rate[0]
                        )
                    )
                pass
            pass
        pass

    # Take VFATs out of run mode
    for ohN in range(0,amcBoard.nOHs):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue

        # update the OH in question
        vfatBoard.parentOH.link = ohN

        #Place chips into run mode
        vfatBoard.setRunModeAll(ohVFATMaskArray[ohN], False, args.debug)
        pass

    printGreen("SBIT Rate scan vs. {0} for optohybrids in 0x{1:x} {2} completed".format(scanReg, args.ohMask, strChannels))

    return
