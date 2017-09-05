def readBackCheck(rootTree, dict_Names, device, gtx):
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
    import ROOT as r
    import sys
    
    # Check that the requested register is supported
    list_KnownRegs = parameters.defaultValues.keys()
    list_KnownRegs.append("VThreshold1")
    list_KnownRegs.append("VFATChannels.ChanReg")
    for regName in dict_Names.values():
        if regName not in list_KnownRegs:
            print "readBackCheck() does not understand %s"%(regName)
            print "readBackCheck() is only supported for registers:", list_KnownRegs
            sys.exit(-1)

    # Get data from tree
    list_bNames = dict_Names.keys()
    list_bNames.append('vfatN')
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
        else: #VFAT Register, use 0xff
            regValues = readAllVFATs(device, gtx, regName, 0x0)
            regMap = map(lambda chip: chip&0xff, regValues)

            for vfat,readBackVal in enumerate(regMap):
                writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
                writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
                if writeValOfReg != readBackVal:
                    print "VFAT%i: %s mismatch, write val = %i, readback = %i"%(vfat, regName, writeValOfReg, readBackVal)

    return
