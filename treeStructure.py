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
        self.gemTree.Branch( 'utime', self.utime, 'utime/i' )
        
        self.ztrim = array( 'f', [ 0 ] )
        self.gemTree.Branch( 'ztrim', self.ztrim, 'ztrim/F' )

        self.calSelPol = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'calSelPol', self.calSelPol, 'calSelPol/I' )

        self.iref = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'iref', self.iref, 'iref/I' )

        self.vfatCH = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vfatCH', self.vfatCH, 'vfatCH/I' )
        
        self.vfatID = array( 'L', [0] )
        self.gemTree.Branch( 'vfatID', self.vfatID, 'vfatID/i' ) #Hex Chip ID of VFAT

        self.vfatN = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'vfatN', self.vfatN, 'vfatN/I' )

        return

    def autoSave(self, option="SaveSelf"):
        self.gemTree.AutoSave(option)
        return

    def getMode(self):
        return self.mode[0]

    def assignBaseValues(self, **kwargs):
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
    def __init__(self, name, nameX, nameY, dacSelect = -1, isGblDac=True, storeRoot=False, description="Generic GEM DAC Calibration Tree"):
        """
        name        TName of the TTree
        dacSelect   DAC selection
        nameX       Register that is being calibrated (dependent variable)
        nameY       Value calibration is being performed against (e.g. scurveMean, or charge)
        isGblDac    DAC is common across entire VFAT (True) or is specific for a given channel (False);
                    if True the vfatCH branch will be written as 128 for all entries
        storeRoot   Store ROOT Objects Associated with this Dac Calibration
        description Phrase describing the TTree
        """
        
        gemGenericTree.__init__(self,name=name,description=description)

        self.dacValX = array( 'f', [0] )
        self.gemTree.Branch( 'dacValX', self.dacValX, 'dacValX/F')

        self.dacValX_Err = array( 'i', [0] )
        self.gemTree.Branch( 'dacValX_Err', self.dacValX_Err, 'dacValX_Err/I')

        self.dacValY = array( 'f', [0] )
        self.gemTree.Branch( 'dacValY', self.dacValY, 'dacValY/F')

        self.dacValY_Err = array( 'i', [0] )
        self.gemTree.Branch( 'dacValY_Err', self.dacValY_Err, 'dacValY_Err/I')

        self.isGblDac = isGblDac
        self.storeRoot = storeRoot

        self.dacSelect = array( 'i', [0] )
        self.gemTree.Branch( 'dacSelect', self.dacSelect, 'dacSelect/I')
        
        self.nameX = r.vector('string')()
        self.nameX.push_back(nameX)
        self.gemTree.Branch( 'nameX', self.nameX)

        self.nameY = r.vector('string')()
        self.nameY.push_back(nameY)
        self.gemTree.Branch( 'nameY', self.nameY)

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

        if "calSelPol" in kwargs:
            self.calSelPol[0] = kwargs["calSelPol"]
        if "dacValX" in kwargs:
            self.dacValX[0] = kwargs["dacValX"]
        if "dacValX_Err" in kwargs:
            self.dacValX_Err[0] = kwargs["dacValX_Err"]
        if "dacValY" in kwargs:
            self.dacValY[0] = kwargs["dacValY"]
        if "dacValY_Err" in kwargs:
            self.dacValY_Err[0] = kwargs["dacValY_Err"]
        if "iref" in kwargs:
            self.iref[0] = kwargs["iref"]
        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "dacSelect" in kwargs:
            self.dacSelect[0] = kwargs["dacSelect"]
        if "nameX" in kwargs:
            self.nameX[0] = kwargs["nameX"]
        if "nameY" in kwargs:
            self.nameY[0] = kwargs["nameY"]
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
                kwargs["g_dacCal"].Copy(self.g_dacCal)
            if "func_dacFit" in kwargs:
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
        self.gemTree.Branch( 'adcTempIntRef', self.adcTempIntRef, 'adcTempIntRef/I')

        self.adcTempExtRef = array('i', [0])
        self.gemTree.Branch( 'adcTempExtRef', self.adcTempExtRef, 'adcTempExtRef/I')

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for
        simplicity.
        """

        if "adcTempIntRef" in kwargs:
            self.adcTempIntRef[0] = kwargs["adcTempIntRef"]
        if "adcTempExtRef" in kwargs:
            self.adcTempExtRef[0] = kwargs["adcTempExtRef"]
        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "utime" in kwargs:
            self.utime[0] = kwargs["utime"]
        if "vfatID" in kwargs:
            self.vfatID[0] = kwargs["vfatID"]
        if "vfatN" in kwargs:
            self.vfatN[0] = kwargs["vfatN"]

        self.gemTree.Fill()
        return

class  gemTemepratureOHTree(gemGenericTree):
    def __init__(self,name="OHTemperatureData",description="OH Temperature Data as a function of time"):
        """
        name        TName of the TTree
        description Phrase describing the TTree
        """

        gemGenericTree.__init__(self,name=name,description=description)

        #self.ohBoardTemp = array('i', [ 0 for x in range(1,10) ])
        #for boardTemp in range(1,10):
        #    self.gemTree.Branch(
        #            "ohBoardTemp{0}".format(boardTemp),
        #            self.ohBoardTemp[boardTemp-1],
        #            "ohBoardTemp{0}/I".format(boardTemp))
        self.ohBoardTemp1 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp1',self.ohBoardTemp1,'ohBoardTemp1/F')

        self.ohBoardTemp2 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp2',self.ohBoardTemp2,'ohBoardTemp2/F')

        self.ohBoardTemp3 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp3',self.ohBoardTemp3,'ohBoardTemp3/F')

        self.ohBoardTemp4 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp4',self.ohBoardTemp4,'ohBoardTemp4/F')

        self.ohBoardTemp5 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp5',self.ohBoardTemp5,'ohBoardTemp5/F')

        self.ohBoardTemp6 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp6',self.ohBoardTemp6,'ohBoardTemp6/F')

        self.ohBoardTemp7 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp7',self.ohBoardTemp7,'ohBoardTemp7/F')

        self.ohBoardTemp8 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp8',self.ohBoardTemp8,'ohBoardTemp8/F')

        self.ohBoardTemp9 = array('f', [0])
        self.gemTree.Branch('ohBoardTemp9',self.ohBoardTemp9,'ohBoardTemp9/F')

        self.scaTemp = array('f', [0])
        self.gemTree.Branch('scaTemp',self.scaTemp, 'scaTemp/F')

        self.fpgaCoreTemp = array('f', [0])
        self.gemTree.Branch('fpgaCoreTemp',self.fpgaCoreTemp,'fpgaCoreTemp/F')

        return

    def fill(self, **kwargs):
        """
        Updates the values stored in the arrays gemTree's branchs map to,
        then it fills the tree.

        The keyword is assumed to the same as the variable name for
        simplicity.
        """

        #for boardTemp in range(1,10):
        #    if "ohBoardTemp{0}".format(boardTemp) in kwargs:
        #        self.ohBoardTemp[boardTemp-1] = kwargs["ohBoardTemp{0}".format(boardTemp)]
        if "ohBoardTemp1" in kwargs:
            self.ohBoardTemp1[0] = kwargs["ohBoardTemp1"]
        if "ohBoardTemp2" in kwargs:
            self.ohBoardTemp2[0] = kwargs["ohBoardTemp2"]
        if "ohBoardTemp3" in kwargs:
            self.ohBoardTemp3[0] = kwargs["ohBoardTemp3"]
        if "ohBoardTemp4" in kwargs:
            self.ohBoardTemp4[0] = kwargs["ohBoardTemp4"]
        if "ohBoardTemp5" in kwargs:
            self.ohBoardTemp5[0] = kwargs["ohBoardTemp5"]
        if "ohBoardTemp6" in kwargs:
            self.ohBoardTemp6[0] = kwargs["ohBoardTemp6"]
        if "ohBoardTemp7" in kwargs:
            self.ohBoardTemp7[0] = kwargs["ohBoardTemp7"]
        if "ohBoardTemp8" in kwargs:
            self.ohBoardTemp8[0] = kwargs["ohBoardTemp8"]
        if "ohBoardTemp9" in kwargs:
            self.ohBoardTemp9[0] = kwargs["ohBoardTemp9"]
        if "fpgaCoreTemp" in kwargs:
            self.fpgaCoreTemp[0] = kwargs["fpgaCoreTemp"]
        if "link" in kwargs:
            self.link[0] = kwargs["link"]
        if "scaTemp" in kwargs:
            self.scaTemp[0] = kwargs["scaTemp"]
        if "utime" in kwargs:
            self.utime[0] = kwargs["utime"]
        if "vfatID" in kwargs:
            self.vfatID[0] = kwargs["vfatID"]
        if "vfatN" in kwargs:
            self.vfatN[0] = kwargs["vfatN"]

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
