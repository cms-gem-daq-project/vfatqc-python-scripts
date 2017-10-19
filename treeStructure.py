import ROOT as r

class gemTreeStructure:
    def __init__(self, name, description="Generic GEM TTree"):
        myT = r.TTree(name,description)

        self.calPhase = array( 'i', [ 0 ] )
        self.myT.Branch( 'calPhase', calPhase, 'calPhase/I' )
        
        self.Dly = array( 'i', [ -1 ] )
        self.myT.Branch( 'Dly', Dly, 'Dly/I' )
        
        self.l1aTime = array( 'i', [ 0 ] )
        self.myT.Branch( 'l1aTime', l1aTime, 'l1aTime/I' )
        
        #self.lat = array( 'i', [ 0 ] )
        #self.myT.Branch( 'lat', lat, 'lat/I' ) #used by ultraLatency
        
        self.latency = array( 'i', [ 0 ] )
        self.myT.Branch( 'latency', latency, 'latency/I' ) #used by ultraScurve, same physical quantity
        
        self.link = array( 'i', [ 0 ] )
        self.myT.Branch( 'link', link, 'link/I' )
        
        self.pDel = array( 'i', [ 0 ] )
        self.myT.Branch( 'pDel', pDel, 'pDel/I' )
        
        self.mode = array( 'i', [ 0 ] )
        self.myT.Branch( 'mode', mode, 'mode/I' )
        
        self.mspl = array( 'i', [ -1 ] )
        self.myT.Branch( 'mspl', mspl, 'mspl/I' )
        
        self.Nev = array( 'i', [ 0 ] )
        self.myT.Branch( 'Nev', Nev, 'Nev/I' )
        
        self.Nhits = array( 'i', [ 0 ] )
        self.myT.Branch( 'Nhits', Nhits, 'Nhits/I' )
        
        self.trimDAC = array( 'i', [ 0 ] )
        self.myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
        
        self.trimRange = array( 'i', [ 0 ] )
        self.myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
        
        self.utime = array( 'i', [ 0 ] )
        self.myT.Branch( 'utime', utime, 'utime/I' )
        
        self.vcal = array( 'i', [ 0 ] )
        self.myT.Branch( 'vcal', vcal, 'vcal/I' )
        
        self.vfatCH = array( 'i', [ 0 ] )
        self.myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
        
        self.vfatN = array( 'i', [ -1 ] )
        self.myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
        
        self.vth = array( 'i', [ 0 ] )
        self.myT.Branch( 'vth', vth, 'vth/I' )
        
        #self.vthr = array( 'i', [ 0 ] )
        #self.myT.Branch( 'vthr', vthr, 'vthr/I' ) # this is vth1, for some reason ultraScurve used different name
        
        self.vth1 = array( 'i', [ 0 ] )
        self.myT.Branch( 'vth1', vth1, 'vth1/I' )
        
        self.vth2 = array( 'i', [ 0 ] )
        self.myT.Branch( 'vth2', vth2, 'vth2/I' )
