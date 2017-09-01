from gempython.tools.vfat_user_functions_uhal import *

import numpy as np
import root_numpy as rp
import ROOT as r
import sys

# rootTree - name of a TTree that has values that should have been written
# dict_Names - dictionary where key names are the branch names in rootTree and the values are the register names they correspond too
# device - optohybrid  the vfats belong to that you want to check
# gtx - link of this optohybrid
def readBackCheck(rootTree, dict_Names, device, gtx):
    # Check that the requested register is supported
    list_KnownRegs = parameters.defaultValues.keys()
    list_KnownRegs.append("VThreshold1")
    for regName in dict_Names.values():
        if regName not in list_KnownRegs:
            print "readBackCheck() does not understand %s"%(regName)
            print "readBackCheck() is only supported for registers:", list_KnownRegs
            sys.exit(-1)

    # Get data from tree
    list_bNames = dict_Names.keys()
    list_bNames.append('vfatN')
    array_writeVals = rp.tree2array(tree=rootTree, branches=list_bNames)

    # Get data from VFATs
    perreg   = "0x%02x"
    for bName,regName in dict_Names.iteritems():
        print "Reading back %s from all VFATs, any potential mismatches will be reported below"%(regName)
        print "="*40
        regValues = readAllVFATs(device, gtx, regName, 0x0)
        regMap = map(lambda chip: chip&0xff, regValues)
        for vfat,readBackVal in enumerate(regMap):
            writeValsPerVFAT = array_writeVals[ array_writeVals['vfatN'] == vfat]
            writeValOfReg = np.asscalar(writeValsPerVFAT['%s'%bName])
            if writeValOfReg != readBackVal:
                print "VFAT%i: %s mismatch, write val = %i, readback = %i"%(vfat, regName, writeValOfReg, readBackVal)
