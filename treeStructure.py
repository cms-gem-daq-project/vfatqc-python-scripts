from array import array
from gempython.tools.optohybrid_user_functions_uhal import scanmode

import sys,os
import ROOT as r

class gemGenericTree(object):
    def __init__(self, name, description="Generic GEM TTree",scanmode=-1):
        """
        scanmode    scan type, e.g. scanmode.<TYPE> parameter
        name        TName of the TTree
        description Phrase describing the TTree
        """

        self.gemTree = r.TTree(name,description)

        self.link = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'link', self.link, 'link/I' )
        
        self.Nev = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'Nev', self.Nev, 'Nev/I' )
        
        self.utime = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'utime', self.utime, 'utime/I' )
        
        self.ztrim = array( 'f', [ 0 ] )
        self.gemTree.Branch( 'ztrim', self.ztrim, 'ztrim/F' )

        self.vfatCH = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vfatCH', self.vfatCH, 'vfatCH/I' )
        
        self.vfatID = array( 'i', [-1] )
        self.gemTree.Branch( 'vfatID', self.vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT

        self.vfatN = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'vfatN', self.vfatN, 'vfatN/I' )

        return

    def autoSave(self, option="SaveSelf"):
        self.gemTree.AutoSave(option)
        return

    def getMode(self):
        return self.mode[0]

    def __assignBaseValues(self, **kwargs):
        """
        Assigns values to the arrays defined in gemTree.__init__().
        Does not fill the tree.

        The keyword is assumed to the same as the variable name for
        simplicity.
        """

        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "Nev" in kwargs:
            self.Nev[0] = kwargs["Nev"]
        if "utime" in kwargs:
            self.utime[0] = kwargs["utime"]
        if (("vfatCH" in kwargs) and (not self.isGblDac)):
            self.vfatCH[0] = kwargs["vfatCH"]
        if "vfatID" in kwargs:
            self.vfatID[0] = kwargs["vfatID"]
        if "vfatN" in kwargs:
            self.vfatN[0] = kwargs["vfatN"]
        if "ztrim" in kwargs:
            self.ztrim[0] = kwargs["ztrim"]

        return

    def setDefaults(self, options, time):
        """
        Takes as input the options object returned by OptParser.parse_args()
        see: https://docs.python.org/2/library/optparse.html

        Sets values common to all scan scripts (see qcoptions.py)
        """

        self.link[0] = options.gtx
        self.Nev[0] = options.nevts
        self.utime[0] = time
        self.ztrim[0] = options.ztrim

        return

    def write(self):
        self.gemTree.Write()
        return

class gemDacCalTreeStructure(gemGenericTree):
    def __init__(self, name, regX, valY, isGblDac=True, storeRoot=False, description="Generic GEM DAC Calibration Tree"):
        """
        name        TName of the TTree
        regX        Register that is being calibrated (dependent variable)
        valY        Value calibration is being performed against (e.g. scurveMean, or charge)
        isGblDac    DAC is common across entire VFAT (True) or is specific for a given channel (False);
                    if True the vfatCH branch will be written as 128 for all entries
        storeRoot   Store ROOT Objects Associated with this Dac Calibration
        description Phrase describing the TTree
        """
        
        gemGenericTree.__init__(self,name=name,description=description)

        self.isGblDac = isGblDac
        self.storeRoot = storeRoot

        self.dacName = regX
        self.gemTree.Branch( 'dacName', self.dacName, 'dacName/C')

        self.dacValX = array( 'i', [0] )
        self.gemTree.Branch( 'dacValX', self.dacValX, 'dacValX/I')

        self.dacValX_Err = array( 'i', [0] )
        self.gemTree.Branch( 'dacValX_Err', self.dacValX, 'dacValX_Err/I')

        self.dacValY = array( 'i', [0] )
        self.gemTree.Branch( 'dacValY', self.dacValY, 'dacValY/I')

        self.dacValY_Err = array( 'i', [0] )
        self.gemTree.Branch( 'dacValY_Err', self.dacValY, 'dacValY_Err/I')
        
        # Set the channel number to 128 Normally 0 to 127
        if self.isGblDac:
            self.vfatCH[0] = 128 
            #branch_vfatCH = self.gemTree.GetBranch('vfatCH')
            #self.gemTree.GetListOfBranches().Remove(branch_vfatCH)

        if self.storeRoot:
            self.g_dacCal = r.TGraphErrors()
            self.gemTree.Branch( 'g_dacCal', self.g_dacCal)
            
            self.func_dacFit = r.TF1()
            self.gemTree.Branch( 'func_dacFit', self.func_dacFit)

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for 
        simplicity.
        """
        
        if "dacValX" in kwargs:
            self.dacValX = kwargs["dacValX"]
        if "dacValX_Err" in kwargs:
            self.dacValX_Err = kwargs["dacValX_Err"]
        if "dacValY" in kwargs:
            self.dacValY = kwargs["dacValY"]
        if "dacValY_Err" in kwargs:
            self.dacValY_Err = kwargs["dacValY_Err"]
        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "Nev" in kwargs:
            self.Nev[0] = kwargs["Nev"]
        if "utime" in kwargs:
            self.utime[0] = kwargs["utime"]
        if (("vfatCH" in kwargs) and (not self.isGblDac)):
            self.vfatCH[0] = kwargs["vfatCH"]
        if "vfatID" in kwargs:
            self.vfatID[0] = kwargs["vfatID"]
        if "vfatN" in kwargs:
            self.vfatN[0] = kwargs["vfatN"]
        if "ztrim" in kwargs:
            self.ztrim[0] = kwargs["ztrim"]

        if self.storeRoot:
            if "g_dacCal" in kwargs:
                #self.g_dacCal = kwargs["g_dacCal"].Clone()
                kwargs["g_dacCal"].Copy(self.g_dacCal)
            if "func_dacFit" in kwargs:
                #self.func_dacFit = kwargs["func_dacFit"].Clone()
                kwargs["func_dacFit"].Copy(self.func_dacFit)

        self.gemTree.Fill()
        return

class  gemTemepratureVFATTree(gemGenericTree):
    def __init__(self,name="VFATTemperatureData",description="VFAT Temperature Data as a function of time"):
        """
        name        TName of the TTree
        description Phrase describing the TTree
        """

        gemGenericTree.__init__(self,name=name,description=description)

        self.adcTempIntRef = array('i', [0])
        self.gemTree.Branch( 'adcTempIntRef', adcTempIntRef, 'adcTempIntRef/I')

        self.adcTempExtRef = array('i', [0])
        self.gemTree.Branch( 'adcTempExtRef', adcTempExtRef, 'adcTempExtRef/I')

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for
        simplicity.
        """

        self.__assignBaseValues(kwargs)

        if "adcTempIntRef" in kwargs:
            self.adcTempIntRef[0] = kwargs["adcTempIntRef"]
        if "adcTempExtRef" in kwargs:
            self.adcTempExtRef[0] = kwargs["adcTempExtRef"]

        self.gemTree.Fill()
        return

class  gemTemepratureOHTree(gemGenericTree):
    def __init__(self,name="OHTemperatureData",description="OH Temperature Data as a function of time"):
        """
        name        TName of the TTree
        description Phrase describing the TTree
        """

        gemGenericTree.__init__(self,name=name,description=description)

        self.scaTemp = array('i', [0])
        self.gemTree.Branch('scaTemp',link, 'scaTemp/I')

        self.fpgaCoreTemp = array('f', [0])
        self.gemTree.Branch('fpgaCoreTemp',fpgaCoreTemp,'fpgaCoreTemp/F')

        self.ohBoardTemp = array('i', [ 0 for x in range(1,10) ])
        for boardTemp in range(1,10):
            self.gemTree.Branch(
                    "ohBoardTemp{0}".format(boardTemp),
                    self.ohBoardTemp[boardTemp-1],
                    "ohBoardTemp{0}/I".format(boardTemp))

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for
        simplicity.
        """

        self.__assignBaseValues(kwargs)

        if "scaTemp" in kwargs:
            self.scaTemp[0] = kwargs["scaTemp"]
        if "fpgaCoreTemp" in kwargs:
            self.fpgaCoreTemp[0] = kwargs["fpgaCoreTemp"]

        for boardTemp im range(1,10):
            if "boardTemp{0}".format(boardTemp) in kwargs:
                self.ohBoardTemp[boardTemp-1] = kwargs["boardTemp{0}".format(boardTemp)]

        self.gemTree.Fill()
        return

class gemTreeStructure(gemGenericTree):
    def __init__(self, name, description="Generic GEM TTree",scanmode=-1):
        """
        scanmode    scan type, e.g. scanmode.<TYPE> parameter
        name        TName of the TTree
        description Phrase describing the TTree
        """
        gemGenericTree.__init__(self,name=name,description=description,scanmode=scanmode)

        self.calPhase = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'calPhase', self.calPhase, 'calPhase/I' )

        self.calSF = array( 'i', [0] )
        self.gemTree.Branch( 'calSF', self.calSF, 'calSF/I')

        self.Dly = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'Dly', self.Dly, 'Dly/I' )

        self.isCurrentPulse = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'isCurrentPulse', self.isCurrentPulse, 'isCurrentPulse/I')
       
        self.isZCC = array( 'i', [0] )
        self.gemTree.Branch( 'isZCC', self.isZCC, 'isZCC/I' )

        self.l1aTime = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'l1aTime', self.l1aTime, 'l1aTime/I' )
        
        self.latency = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'latency', self.latency, 'latency/I' ) #used by ultraScurve, same physical quantity
        
        self.pDel = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'pDel', self.pDel, 'pDel/I' )
        
        self.mode = array( 'i', [ 0 ] )
        self.mode[0] = scanmode
        self.gemTree.Branch( 'mode', self.mode, 'mode/I' )
        
        self.mspl = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'mspl', self.mspl, 'mspl/I' )
        
        self.Nhits = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'Nhits', self.Nhits, 'Nhits/I' )
        
        self.trimDAC = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'trimDAC', self.trimDAC, 'trimDAC/I' )

        self.trimPolarity = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'trimPolarity', self.trimPolarity, 'trimPolarity/I' )

        self.trimRange = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'trimRange', self.trimRange, 'trimRange/I' )
        
        self.vcal = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vcal', self.vcal, 'vcal/I' )
        
        self.vth = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth', self.vth, 'vth/I' )
        
        self.vth1 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth1', self.vth1, 'vth1/I' )
        
        self.vth2 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth2', self.vth2, 'vth2/I' )
    
        self.vthr = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vthr', self.vthr, 'vthr/I' )

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for 
        simplicity.
        """
        
        if "calPhase" in kwargs:
            self.calPhase[0] = kwargs["calPhase"]
        if "calSF" in kwargs:
            self.calSF[0] = kwargs["calSF"]
        if "Dly" in kwargs:
            self.Dly[0] = kwargs["Dly"]
        if "isCurrentPulse" in kwargs:
            self.isCurrentPulse[0] = kwargs["isCurrentPulse"]
        if "isZCC" in kwargs:
            self.isZCC[0] = kwargs["isZCC"]
        if "l1aTime" in kwargs:
            self.l1aTime[0] = kwargs["l1aTime"]
        if "latency" in kwargs:
            self.latency[0] = kwargs["latency"]
        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "pDel" in kwargs:
            self.pDel[0] = kwargs["pDel"]
        if "mspl" in kwargs:
            self.mspl[0] = kwargs["mspl"]
        if "Nev" in kwargs:
            self.Nev[0] = kwargs["Nev"]
        if "Nhits" in kwargs:
            self.Nhits[0] = kwargs["Nhits"]
        if "trimDAC" in kwargs:
            self.trimDAC[0] = kwargs["trimDAC"]
        if "trimPolarity" in kwargs:
            self.trimPolarity[0] = kwargs["trimPolarity"]
        if "trimRange" in kwargs:
            self.trimRange[0] = kwargs["trimRange"]
        if "utime" in kwargs:
            self.utime[0] = kwargs["utime"]
        if "vcal" in kwargs:
            self.vcal[0] = kwargs["vcal"]
        if "vfatCH" in kwargs:
            self.vfatCH[0] = kwargs["vfatCH"]
        if "vfatID" in kwargs:
            self.vfatID[0] = kwargs["vfatID"]
        if "vfatN" in kwargs:
            self.vfatN[0] = kwargs["vfatN"]
        if "vth" in kwargs:
            self.vth[0] = kwargs["vth"]
        if "vth1" in kwargs:
            self.vth1[0] = kwargs["vth1"]
        if "vth2" in kwargs:
            self.vth2[0] = kwargs["vth2"]
        if "vthr" in kwargs:
            self.vthr[0] = kwargs["vthr"]
        if "ztrim" in kwargs:
            self.ztrim[0] = kwargs["ztrim"]

        self.gemTree.Fill()
        return
