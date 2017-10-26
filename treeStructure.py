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

    def fill(self):
        self.gemTree.Fill()
        return

    def getMode(self):
        return self.mode[0]

    def setDefaults(self, options):
        """
        Takes as input the options object returned by OptParser.parse_args()
        see: https://docs.python.org/2/library/optparse.html

        Sets values common to all scan scripts (see qcoptions.py)
        """

        self.link[0] = options.gtx
        self.mspl[0] = options.MSPL
        self.ztrim[0] = options.ztrim
        self.Nev[0] = options.nevts

        return

    def setScanResults(self, dacValue, Nhits):
        """
        For each scan mode sets the appropriate dacValue (e.g. VThreshold1)
        and Nhits determined by the scan module
        """
        self.Nhits[0] = Nhits

        if self.mode[0] == scanmode.THRESHTRG or self.mode[0] == scanmode.THRESHCH or self.mode[0] == scanmode.THRESHTRK:
            self.vth1[0] = dacValue
        elif self.mode[0] == scanmode.SCURVE:
            self.vcal[0] = dacValue
        elif self.mode[0] == scanmode.LATENCY:
            self.latency[0] = dacValue
        else:
            print "scanmode %i not understood"%(self.mode[0])
            print "Available scan modes are:"
            print "\tThreshold scan: %i"%(scanmode.THRESHTRG)
            print "\tThreshold scan per channel: %i"%(scanmode.THRESHCH)
            print "\tLatency scan: %i"%(scanmode.LATENCY)
            print "\tThreshold scan with tracking data: %i"%(scanmode.THRESHTRK)
            exit(os.EX_USAGE)

    def write(self):
        self.gemTree.Write()
        return
