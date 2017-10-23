from array import array
import ROOT as r
#import time

class gemTreeStructure:
    def __init__(self, name, description="Generic GEM TTree"):
        self.gemTree = r.TTree(name,description)

        self.calPhase = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'calPhase', self.calPhase, 'calPhase/I' )
        
        self.Dly = array( 'i', [ -1 ] )
        self.gemTree.Branch( 'Dly', self.Dly, 'Dly/I' )
        
        self.l1aTime = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'l1aTime', self.l1aTime, 'l1aTime/I' )
        
        #self.lat = array( 'i', [ 0 ] )
        #self.gemTree.Branch( 'lat', lat, 'lat/I' ) #used by ultraLatency
        
        self.latency = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'latency', self.latency, 'latency/I' ) #used by ultraScurve, same physical quantity
        
        self.link = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'link', self.link, 'link/I' )
        
        self.pDel = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'pDel', self.pDel, 'pDel/I' )
        
        self.mode = array( 'i', [ 0 ] )
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
        
        #self.vthr = array( 'i', [ 0 ] )
        #self.gemTree.Branch( 'vthr', vthr, 'vthr/I' ) # this is vth1, for some reason ultraScurve used different name
        
        self.vth1 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth1', self.vth1, 'vth1/I' )
        
        self.vth2 = array( 'i', [ 0 ] )
        self.gemTree.Branch( 'vth2', self.vth2, 'vth2/I' )
