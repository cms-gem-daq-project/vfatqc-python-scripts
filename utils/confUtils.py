def configure(args, vfatBoard):
    """
    Configures the front-end detector

    args - namespace returned by ArgumentParser::parse_args(), expects to contain following fields:

        chConfig    - Text file containing the channel configuration register information
        compare     - If True only compares provided config file(s) with currently loaded parameters in frontend, does not write
        debug       - Prints additional debugging information
        gtx         - OH number
        filename    - TFile containing the scurveFitTree, used in writing channel registers
        run         - Places front-end ASIC into run mode if true
        vt1         - For V3 (V2) electronics this is CFG_THR_ARM_DAC (VThreshold1) value to write
        vt1bump     - Adds this value to the CFG_THR_ARM_DAC or VThreshold1 value that will be written
        vt2         - For V3 (V2) electronics this is not used (VThreshold2 value to write)
        vfatConfig  - For V3 (V2) electronics contains CFG_THR_ARM_DAC (VThreshold1 & trimRange) values to write per VFAT
        vfatmask    - 24 bit number specifying which vfats to mask, a 1 in the N^th bit means ignore that vfat
        zeroChan    - Sets all bits of all channel registers to 0

    vfatBoard - An instance of HwVFAT class
    """

    if args.gtx in chamber_vfatDACSettings.keys():
        print "Configuring VFATs with chamber_vfatDACSettings dictionary values"
        for key in chamber_vfatDACSettings[args.gtx]:
            vfatBoard.paramsDefVals[key] = chamber_vfatDACSettings[args.gtx][key]
    vfatBoard.biasAllVFATs(args.vfatmask)
    print 'biased VFATs'
    
    if not args.compare:
        vfatBoard.setVFATThresholdAll(args.vfatmask, args.vt1, args.vt2)
        if vfatBoard.parentOH.parentAMC.fwVersion > 2:
            print('Set CFG_THR_ARM_DAC to %i'%args.vt1)
        else:
            print('Set VThreshold1 to %i'%args.vt1)
            print('Set VThreshold2 to %i'%args.vt2)
    
    if args.run:
        vfatBoard.setRunModeAll(args.vfatmask, True)
        print 'VFATs set to run mode'
    else:
        vfatBoard.setRunModeAll(args.vfatmask, False)
    
    import ROOT as r
    if args.filename:
        try:
            inF = r.TFile(args.filename)
            chTree = inF.Get("scurveFitTree")
            if not args.compare:
                print 'Configuring Channel Registers based on %s'%args.filename        
                setChannelRegisters(vfatBoard, chTree, args.vfatmask)

            dict_readBack = {}
            if vfatBoard.parentOH.parentAMC.fwVersion > 2:
                dict_readBack = { "trimDAC":"VFAT_CHANNELS.CHANNEL", "trimPolarity":"VFAT_CHANNELS.CHANNEL", "mask":"VFAT_CHANNELS.CHANNEL", "vfatID":"HW_CHIP_ID" }
                print 'Comparing Currently Stored Channel Registers with %s'%args.chConfig
                readBackCheckV3(chTree, dict_readBack, vfatBoard, args.vfatmask)
    
        except Exception as e:
            print '%s does not seem to exist'%args.filename
            print e
    
    if args.chConfig:
        try:
            chTree = r.TTree('chTree','Tree holding Channel Configuration Parameters')
            chTree.ReadFile(args.chConfig)
            if not args.compare:
                print 'Configuring Channel Registers based on %s'%args.chConfig
                setChannelRegisters(vfatBoard, chTree, args.vfatmask)

            dict_readBack = {}
            if vfatBoard.parentOH.parentAMC.fwVersion > 2:
                dict_readBack = { "trimDAC":"VFAT_CHANNELS.CHANNEL", "trimPolarity":"VFAT_CHANNELS.CHANNEL", "mask":"VFAT_CHANNELS.CHANNEL", "vfatID":"HW_CHIP_ID" }
                print 'Comparing Currently Stored Channel Registers with %s'%args.chConfig
                readBackCheckV3(chTree, dict_readBack, vfatBoard, args.vfatmask)
    
        except Exception as e:
            print '%s does not seem to exist'%args.filename
            print e
    
    if args.zeroChan:    
        print("zero'ing all channel registers")    
        rpcResp = vfatBoard.setAllChannelRegisters(vfatMask=args.vfatmask)
                    
        if rpcResp != 0:
            raise Exception("RPC response was non-zero, zero'ing all channel registers failed")
        pass
    
    if args.vfatConfig:
        try:
            vfatTree = r.TTree('vfatTree','Tree holding VFAT Configuration Parameters')
            vfatTree.ReadFile(args.vfatConfig)
    
            if not args.compare:
                print 'Configuring VFAT Registers based on %s'%args.vfatConfig
    
                for event in vfatTree :
                    # Skip masked vfats
                    if (args.vfatmask >> int(event.vfatN)) & 0x1:
                        continue
                    
                    # Tell user whether CFG_THR_ARM_DAC or VThreshold1 is being written
                    if vfatBoard.parentOH.parentAMC.fwVersion > 2:
                        print 'Set link %d VFAT%d CFG_THR_ARM_DAC to %i'%(args.gtx,event.vfatN,event.vt1+args.vt1bump)
                    else:
                        print 'Set link %d VFAT%d VThreshold1 to %i'%(args.gtx,event.vfatN,event.vt1+args.vt1bump)
                    
                    # Write CFG_THR_ARM_DAC or VThreshold1
                    vfatBoard.setVFATThreshold(chip=int(event.vfatN), vt1=int(event.vt1+args.vt1bump))
    
                    # Write trimRange (only supported for v2b electronics right now)
                    if not (vfatBoard.parentOH.parentAMC.fwVersion > 2):
                        vfatBoard.writeVFAT(int(event.vfatN), "ContReg3", int(event.trimRange),args.debug)
            
            if vfatBoard.parentOH.parentAMC.fwVersion > 2:
                print 'Comparing Curently Stored VFAT Registers with %s'%args.vfatConfig
                dict_readBack = { "vfatID":"HW_CHIP_ID", "vt1":"CFG_THR_ARM_DAC" }
                readBackCheck(vfatTree, dict_readBack, vfatBoard, args.vfatmask, args.vt1bump)
    
        except Exception as e:
            print '%s does not seem to exist'%args.filename
            print e
def getChannelRegisters(vfatBoard, mask):
    """
    Returns a structured numpy array that stores the channel
    register information.  The dtypes of the output numpy array
    are:

        CALPULSE_ENABLE
        MASK
        ZCC_TRIM_POLARITY
        ZCC_TRIM_AMPLITUDE
        ARM_TRIM_POLARITY
        ARM_TRIM_AMPLITUDE
   
    The numpy array will have an index that goes as:

        idx = 128 * vfatN + channel

    vfatBoard - an instance of the HwVFAT class
    mask - vfat mask to apply
    """
    
    import os
    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
        raise Exception("getChannelRegisters() does not support for v2b electronics", os.EX_USAGE)

    chanRegData = vfatBoard.getAllChannelRegisters(mask)

    import numpy as np
    dataType=[
            ('CALPULSE_ENABLE','bool'),
            ('MASK','bool'),
            ('ZCC_TRIM_POLARITY','bool'),
            ('ZCC_TRIM_AMPLITUDE','uint8'),
            ('ARM_TRIM_POLARITY','bool'),
            ('ARM_TRIM_AMPLITUDE','uint8')]
    chanRegArray = np.zeros(3072, dtype=dataType)

    for idx in range(0,3072):
        if (mask >> (idx // 128) ) & 0x1:
            continue
        chanRegArray[idx]['CALPULSE_ENABLE'] = (chanRegData[idx] >> 15) & 0x1
        chanRegArray[idx]['MASK'] = (chanRegData[idx] >> 14) & 0x1
        chanRegArray[idx]['ZCC_TRIM_POLARITY'] = (chanRegData[idx] >> 13) & 0x1
        chanRegArray[idx]['ARM_TRIM_POLARITY'] = (chanRegData[idx] >> 6) & 0x1
        chanRegArray[idx]['ARM_TRIM_AMPLITUDE'] = chanRegData[idx] & 0x3F

    return chanRegArray

def readBackCheck(rootTree, dict_Names, device, gtx, vt1bump=0):
    """
    Given an input set of registers, and expected values of those registers, read from all VFATs on device.gtx to see if there are any differences between written and read values.

    rootTree - name of a TTree that has values that should have been written
    dict_Names - dictionary where key names are the branch names in rootTree and the values are the register names they correspond too
    device - optohybrid the vfats belong to that you want to check
    gtx - link of this optohybrid
    """

    from gempython.tools.vfat_user_functions_uhal import *
    
    import numpy as np
    import root_numpy as rp
    import sys
    
    # Check that the requested register is supported
    list_KnownRegs = parameters.defaultValues.keys()
    list_KnownRegs.append("VThreshold1")
    list_KnownRegs.append("VFATChannels.ChanReg")
    list_KnownRegs.append("ChipID")
    for regName in dict_Names.values():
        if regName not in list_KnownRegs:
            raise Exception("readBackCheck() does not understand {0}; only supported for registers: {1}".format(regName, list_KnownRegs),os.EX_USAGE)

    # Get data from tree
    list_bNames = dict_Names.keys()
    list_bNames.append('vfatN')
    list_bNames.append('vfatID')
    if "trimDAC" in dict_Names.keys() or "mask" in dict_Names.keys():
        list_bNames.append('vfatCH')
    array_writeVals = rp.tree2array(tree=rootTree, branches=list_bNames)

    # Get data from VFATs
    perreg   = "0x%02x"
    for bName,regName in dict_Names.iteritems():
        print "Reading back (%s,%s) from all VFATs, any potential mismatches will be reported below"%(bName,regName)
        print "="*40
        
        regMap = []
        regValues = []
        if regName == "VFATChannels.ChanReg": #Channel Register, use 0x1f
            for chan in range(0,128):
                regValues = readAllVFATs(device, gtx, regName+"%d"%(chan), 0x0)
                #regMap = map(lambda chip: chip&0x1f, regValues)
                
                for vfat,readBackVal in enumerate(regValues):
                    writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                    writeValsPerVFAT = writeValsPerVFAT[ writeValsPerVFAT['vfatCH'] == chan]
                    writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName]) 
                    if bName == "mask":
                        if writeValOfReg != ((readBackVal&0x20)%31): #trimDAC goes from 0 -> 31, leftover is mask
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, (readBackVal&0x20)%31)
                    else:
                        if writeValOfReg != (readBackVal&0x1f):
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, readBackVal&0x1f)
        elif regName == "ChipID": #ChipID
            regValues = getAllChipIDs(device, gtx, 0x0) # dict of { vfatN:chipID }
            for vfat in regValues:
                valsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                valOfReg = np.asscalar(np.unique(valsPerVFAT['%s'%bName]))
                if valOfReg != regValues[vfat]:
                    print "VFAT%i: %s mismatch, expected = %s, readback = %s"%(vfat, regName, hex(valOfReg), hex(regValues[vfat]))
        else: #VFAT Register, use 0xff
            regValues = readAllVFATs(device, gtx, regName, 0x0)
            regMap = map(lambda chip: chip&0xff, regValues)

            for vfat,readBackVal in enumerate(regMap):
                writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
                if regName == "VThreshold1":
                    writeValOfReg+=vt1bump
                if writeValOfReg != readBackVal:
                    print "VFAT%i: %s mismatch, write val = %i, readback = %i"%(vfat, regName, writeValOfReg, readBackVal)

    return

def readBackCheckV3(rootTree, dict_Names, vfatBoard, mask=0x0, vt1bump=0):
    """
    Given an input set of registers, and expected values of those registers, read from all VFATs on vfatBoard to see if there are any differences between written and read values.  Specifically for v3 electronics

    rootTree - name of a TTree that has values that should have been written
    dict_Names - dictionary where key names are the branch names in rootTree and the values are the register names they correspond too
    vfatBoard - instance of the HwVFAT class
    mask - vfatmask to use, 24 bit number, if the n^th bit is 1 the n^th VFAT is not considered
    vt1bump - value that has been added to CFG_THR_ARM_DAC
    """

    import numpy as np
    import root_numpy as rp
    import os, sys

    # Check that the requested register is supported
    list_KnownRegs = [
            "CFG_PULSE_STRETCH",
            "CFG_SYNC_LEVEL_MODE",
            "CFG_SELF_TRIGGER_MODE",
            "CFG_DDR_TRIGGER_MODE",
            "CFG_SPZS_SUMMARY_ONLY",
            "CFG_SPZS_MAX_PARTITIONS",
            "CFG_SPZS_ENABLE",
            "CFG_SZP_ENABLE",
            "CFG_SZD_ENABLE",
            "CFG_TIME_TAG",
            "CFG_EC_BYTES",
            "CFG_BC_BYTES",
            "CFG_FP_FE",
            "CFG_RES_PRE",
            "CFG_CAP_PRE",
            "CFG_PT",
            "CFG_EN_HYST",
            "CFG_SEL_POL",
            "CFG_FORCE_EN_ZCC",
            "CFG_FORCE_TH",
            "CFG_SEL_COMP_MODE",
            "CFG_VREF_ADC",
            "CFG_MON_GAIN",
            "CFG_MONITOR_SELECT",
            "CFG_IREF",
            "CFG_THR_ZCC_DAC",
            "CFG_THR_ARM_DAC",
            "CFG_HYST",
            "CFG_LATENCY",
            "CFG_CAL_SEL_POL",
            "CFG_CAL_PHI",
            "CFG_CAL_EXT",
            "CFG_CAL_DAC",
            "CFG_CAL_MODE",
            "CFG_CAL_FS",
            "CFG_CAL_DUR",
            "CFG_BIAS_CFD_DAC_2",
            "CFG_BIAS_CFD_DAC_1",
            "CFG_BIAS_PRE_I_BSF",
            "CFG_BIAS_PRE_I_BIT",
            "CFG_BIAS_PRE_I_BLCC",
            "CFG_BIAS_PRE_VREF",
            "CFG_BIAS_SH_I_BFCAS",
            "CFG_BIAS_SH_I_BDIFF",
            "CFG_BIAS_SH_I_BFAMP",
            "CFG_BIAS_SD_I_BDIFF",
            "CFG_BIAS_SD_I_BSF",
            "CFG_BIAS_SD_I_BFCAS",
            "CFG_RUN",
            "HW_CHIP_ID",
            "VFAT_CHANNELS.CHANNEL"]

    for regName in dict_Names.values():
        if regName not in list_KnownRegs:
            raise Exception("readBackCheckV3() does not understand {0}; only supported for registers: {1}".format(regName, list_KnownRegs),os.EX_USAGE)

    # Get data from tree
    list_bNames = dict_Names.keys()
    list_bNames.append('vfatN')
    if "mask" in dict_Names.keys() or "trimDAC" in dict_Names.keys() or "trimPolarity" in dict_Names.keys():
        list_bNames.append('vfatCH')
    array_writeVals = rp.tree2array(tree=rootTree, branches=list_bNames)

    # Get data from VFATs
    for bName,regName in dict_Names.iteritems():
        print "Reading back (%s,%s) from all VFATs, any potential mismatches will be reported below"%(bName,regName)
        print "="*40

        regMap = []
        regValues = []
        if regName == "VFAT_CHANNELS.CHANNEL": #Channel Register
            regValues = getChannelRegisters(vfatBoard,mask)
            for vfat in range(0,24):
                if (mask >> vfat) & 0x1:
                    continue

                for chan in range(0,128):
                    writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                    writeValsPerVFAT = writeValsPerVFAT[ writeValsPerVFAT['vfatCH'] == chan]
                    writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
                    if bName == "mask":
                        if writeValOfReg != regValues[128*vfat+chan]['MASK']:
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, regValues[128*vfat+chan]['MASK'])
                    elif bName == "trimDAC":
                        if writeValOfReg != regValues[128*vfat+chan]['ARM_TRIM_AMPLITUDE']:
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, regValues[128*vfat+chan]['ARM_TRIM_AMPLITUDE'])
                    elif bName == "trimPolarity":
                        if writeValOfReg != regValues[128*vfat+chan]['ARM_TRIM_POLARITY']:
                            print "VFAT%i Chan%i: %s mismatch, write val = %i, readback = %i"%(vfat, chan, bName, writeValOfReg, regValues[128*vfat+chan]['ARM_TRIM_POLARITY'])
        elif regName == "HW_CHIP_ID": #ChipID
            regValues = vfatBoard.getAllChipIDs(mask)
            for vfat,readBackVal in enumerate(regValues):
                if (mask >> vfat) & 0x1:
                    continue
                valsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                valOfReg = np.asscalar(np.unique(valsPerVFAT['%s'%bName]))
                if valOfReg != readBackVal:
                    print "VFAT%i: %s mismatch, expected = %s, readback = %s"%(vfat, regName, hex(valOfReg), hex(readBackVal))
        else: #VFAT Register
            regValues = vfatBoard.readAllVFATs(regName, mask)
            for vfat,readBackVal in enumerate(regValues):
                if (mask >> vfat) & 0x1:
                    continue
                writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
                if regName == "CFG_THR_ARM_DAC":
                    writeValOfReg+=vt1bump
                if writeValOfReg != readBackVal:
                    print "VFAT%i: %s mismatch, write val = %i, readback = %i"%(vfat, regName, writeValOfReg, readBackVal)

    return

def setChannelRegisters(vfatBoard, chTree, mask, debug=False):
    """
    vfatBoard - an instance of the HwVFAT class
    chTree - TTree generated from a chConfig.txt file
    mask - vfat mask to apply
    debug - print additional information if True
    """

    from ctypes import *
    
    # Make the cArrays
    cArray_Masks = (c_uint32 * 3072)()
    cArray_trimVal = (c_uint32 * 3072)()
    cArray_trimPol = (c_uint32 * 3072)()

    for event in chTree :
        # Skip masked vfats
        if (mask >> int(event.vfatN)) & 0x1:
            continue

        if (vfatBoard.parentOH.parentAMC.fwVersion > 2):
            cArray_Masks[128*event.vfatN+event.vfatCH] = event.mask
            cArray_trimVal[128*event.vfatN+event.vfatCH] = event.trimDAC
            cArray_trimPol[128*event.vfatN+event.vfatCH] = event.trimPolarity
        else:
            if int(event.vfatCH) == 0:
                vfatBoard.writeVFAT(ohboard, options.gtx, int(event.vfatN), "ContReg3", int(event.trimRange),options.debug)
            if event.mask==0 and event.trimDAC==0:
                continue
            vfatBoard.setChannelRegister(chip=int(event.vfatN), chan=int(event.vfatCH), mask=int(event.mask), trimARM=int(event.trimDAC), debug=options.debug)
            pass
        pass
    
    if (vfatBoard.parentOH.parentAMC.fwVersion > 2):
        rpcResp = vfatBoard.setAllChannelRegisters(
                chMask=cArray_Masks,
                trimARM=cArray_trimVal,
                trimARMPol=cArray_trimPol,
                vfatMask=mask,
                debug=debug)

        if rpcResp != 0:
            raise Exception("RPC response was non-zero, setting trim values for all channels failed")
        pass

    return
