from ctypes import *

from gempython.tools.amc_user_functions_xhal import maxVfat3DACSize
from gempython.tools.vfat_user_functions_xhal import *

def dacScanAllLinks(args, calTree, vfatBoard):
    """
    Performs a DAC scan on all VFATs on all unmasked OH's on amcBoard

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instance of HwVFAT
    """

    # Get the AMC
    amcBoard = vfatBoard.parentOH.parentAMC

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
    for ohN in range(0,12):
        # Skip masked OH's
        if( not ((args.ohMask >> ohN) & 0x1)):
            calSelPolVals[ohN] = [ 0 for vfat in range(0,24) ]
            irefVals[ohN] = [ 0 for vfat in range(0,24) ]
            vfatIDvals[ohN] = [ 0 for vfat in range(0,24) ]
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
    arraySize = amcBoard.nOHs * (dacMax-dacMin+1)*24/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Scanning DAC: {0} on all links".format(maxVfat3DACSize[dacSelect][1]))
    rpcResp = amcBoard.performDacScanMultiLink(scanData,dacSelect,args.stepSize,args.ohMask,args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    #try:
    if args.debug:
        print("| link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :--: | :---: | :----: | :-------: |:-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
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

    print("DAC scans for optohybrids in {0} completed".format(args.ohMask))

    return

def dacScanSingleLink(args, calTree, vfatBoard):
    """
    Performs a DAC scan for the VFATs on the OH that vfatBoard.parentOH corresponds too

    args - parsed arguments from an ArgumentParser instance
    calTree - instance of gemDacCalTreeStructure
    vfatBoard - instace of HwVFAT
    """

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
    arraySize = (dacMax-dacMin+1)*24/args.stepSize
    scanData = (c_uint32 * arraySize)()
    print("Scanning DAC {0} on Optohybrid {1}".format(maxVfat3DACSize[dacSelect][1], vfatBoard.parentOH.link))
    rpcResp = vfatBoard.parentOH.performDacScan(scanData, dacSelect, args.stepSize, args.vfatmask, args.extRefADC)
    if rpcResp != 0:
        raise Exception('RPC response was non-zero, this inidcates an RPC exception occurred')

    # Store Data
    calTree.link[0] = vfatBoard.parentOH.link

    #try:
    if args.debug:
        print("| link | vfatN | vfatID | dacSelect | nameX | dacValX | dacValX_Err | nameY | dacValY | dacValY_Err |")
        print("| :--: | :---: | :----: | :-------: | :-----: | :-----: | :---------: | :--: | :-----: | :---------: |")
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
            print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} |".format(
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

    print("DAC scan for optohybrid {0} completed".format(vfatBoard.parentOH.link))

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
    vfatmask = 0x0
    voltageStepPulse = False
    trimARM = None
    trimARMPol = None
    trimZCC = None
    trimZCCPol = None

    # Get defaults from kwargs
    if "calSF" in kwargs:
        calSF = kwargs["calSF"]
    if "cardName" in kwargs:
        cardName = kwargs["cardName"]
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

    # Check minimum arguments
    import os
    if cardName is None:
        raise Exception("launchSCurve(): You must provide either an AMC network alias (e.g. 'eagle60') or an AMC ip address.",os.EX_USAGE)
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
            "--cardName=%s"%(cardName),
            "-g%d"%(link),
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

    # launch the command
    from gempython.utils.wrappers import runCommand
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

