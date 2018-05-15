from array import array
from gempython.tools.optohybrid_user_functions_uhal import scanmode

import sys,os
import ROOT as r

class gemTreeStructure:
    def __init__(self, name, description="Generic GEM TTree",scanmode=-1):
        """
        scanmode    scan type, e.g. scanmode.<TYPE> parameter
        name        TName of the TTree
        description Phrase describing the TTree
        """

        self.gemTree = r.TTree(name,description)

        self.calPhase = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'calPhase', self.calPhase, 'calPhase/I' )
        
        self.Dly = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'Dly', self.Dly, 'Dly/I' )
        
        self.l1aTime = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'l1aTime', self.l1aTime, 'l1aTime/I' )
        
        self.latency = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'latency', self.latency, 'latency/I' ) #used by ultraScurve, same physical quantity
        
        self.link = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'link', self.link, 'link/I' )
        
        self.pDel = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'pDel', self.pDel, 'pDel/I' )
        
        self.mode = array( 'i', [ 0 ] )
        self.mode[0] = scanmode
        self.gemTree.Branch( 'mode', self.mode, 'mode/I' )
        
        self.mspl = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'mspl', self.mspl, 'mspl/I' )
        
        self.Nev = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'Nev', self.Nev, 'Nev/I' )
        
        self.Nhits = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'Nhits', self.Nhits, 'Nhits/I' )
        
        self.trimDAC = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'trimDAC', self.trimDAC, 'trimDAC/I' )
        
        self.trimRange = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'trimRange', self.trimRange, 'trimRange/I' )
        
        self.utime = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'utime', self.utime, 'utime/I' )
        
        self.vcal = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vcal', self.vcal, 'vcal/I' )
        
        self.vfatCH = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vfatCH', self.vfatCH, 'vfatCH/I' )
        
        self.vfatID = array( 'i', [-1] )
        self.gemTree.Branch( 'vfatID', vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT

        self.vfatN = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'vfatN', self.vfatN, 'vfatN/I' )
        
        self.vth = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth', self.vth, 'vth/I' )
        
        self.vth1 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth1', self.vth1, 'vth1/I' )
        
        self.vth2 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth2', self.vth2, 'vth2/I' )

        self.ztrim = array( 'f', [ 0 ] )
        self.gemTree.Branch( 'ztrim', self.ztrim, 'ztrim/F' )

        return

    def autoSave(self, option="SaveSelf"):
        self.gemTree.AutoSave(option)
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
        if "Dly" in kwargs:
            self.Dly[0] = kwargs["Dly"]
        if "l1aTime" in kwargs:
            self.l1aTime[0] = kwargs["l1aTime"]
        if "latency" in kwargs:
            self.latency[0] = kwargs["latency"]
        if "link" in kwargs:
            self.link[0] = kwargs["kwargs"]
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
        if "ztrim" in kwargs:
            self.ztrim[0] = kwargs["ztrim"]

        self.gemTree.Fill()
        return

    def getMode(self):
        return self.mode[0]
    
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
