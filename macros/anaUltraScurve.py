import os
from optparse import OptionParser
from array import array
from fitScanData import *
from channelMaps import *
from ROOT import TFile,TTree,TH2D,TGraph,TGraph2D,TCanvas,TPad,gROOT,gStyle,gPad,TPaveStats

parser = OptionParser()

parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename", default="SCurveFitData.root",
                  help="Specify Output Filename", metavar="outfilename")
parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                  help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                  help="Specify GEB (long/short)", metavar="GEBtype")
parser.add_option("-f", "--fit", action="store_true", dest="SaveFile",
                  help="Save the Fit values to Root file", metavar="SaveFile")
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")


(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename
gROOT.SetBatch(True)
#gStyle.SetOptStat(0)
GEBtype = options.GEBtype
inF = TFile(filename+'.root')

if options.SaveFile:
    outF = TFile(filename+'/'+outfilename, 'recreate')
    myT = TTree('scurveFitTree','Tree Holding FitData')
    pass
#Build the channel to strip mapping from the text file
lookup_table = []
for vfat in range(0,24):
    lookup_table.append([])
    for channel in range(0,128):
        lookup_table[vfat].append(0)
        pass
    pass

buildHome = os.environ.get('BUILD_HOME')

if GEBtype == 'long':
    intext = open(buildHome+'/vfatqc-python-scripts/macros/longChannelMap.txt', 'r')
    for i, line in enumerate(intext):
        if i == 0: continue
        mapping = line.rsplit('\t')
        lookup_table[int(mapping[0])][int(mapping[2]) -1] = int(mapping[1])
        pass
    pass
if GEBtype == 'short':
    intext = open(buildHome+'/vfatqc-python-scripts/macros/shortChannelMap.txt', 'r')
    for i, line in enumerate(intext):
        if i == 0: continue
        mapping = line.rsplit('\t')
        lookup_table[int(mapping[0])][int(mapping[2]) -1] = int(mapping[1])
        pass
    pass

if options.SaveFile:
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    vfatstrip = array( 'i', [ 0 ] )
    myT.Branch( 'vfatstrip', vfatstrip, 'vfatstrip/I' )
    trimRange = array( 'i', [ 0 ] )
    myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
    vthr = array( 'i', [ 0 ] )
    myT.Branch( 'vthr', vthr, 'vthr/I' )
    trimDAC = array( 'i', [ 0 ] )
    myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
    threshold = array( 'f', [ 0 ] )
    myT.Branch( 'threshold', threshold, 'threshold/F')
    noise = array( 'f', [ 0 ] )
    myT.Branch( 'noise', noise, 'noise/F')
    pedestal = array( 'f', [ 0 ] )
    myT.Branch( 'pedestal', pedestal, 'pedestal/F')
    ped_eff = array( 'f', [ 0 ] )
    myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
    scurve_h = TH1D()
    myT.Branch( 'scurve_h', scurve_h)
    chi2 = array( 'f', [ 0 ] )
    myT.Branch( 'chi2', chi2, 'chi2/F')
    pass

vSum = {}
vScurves = []
#scruve[vfat][channel][vcal of this event] = Nhits
vthr_list = []
trim_list = []
trimrange_list = []
def overlay_fit(VFAT, CH):
    Scurve = TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CH),255,-0.5,254.5)
    strip = lookup_table[VFAT][CH]
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    param0 = scanFits[0][VFAT][CH]
    param1 = scanFits[1][VFAT][CH]
    param2 = scanFits[2][VFAT][CH]
    fitTF1 =  TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    fitTF1.SetParameter(2, param2)
    canvas = TCanvas('canvas', 'canvas', 500, 500)
    gStyle.SetOptStat(1111111)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, strip))
    return



for i in range(0,24):
    vScurves.append([])
    vthr_list.append([])
    trim_list.append([])
    trimrange_list.append([])
    if not options.channels:
        vSum[i] = TH2D('vSum%i'%i,'vSum%i;Strip;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
        pass
    else:
        vSum[i] = TH2D('vSum%i'%i,'vSum%i;Channels;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
        pass
    for ch in range (0,128):
        vScurves[i].append(TH1D('Scurve_%i_%i'%(i,ch),'Scurve_%i_%i;VCal [DAC units]'%(i,ch),256,-0.5,255.5))
        vthr_list[i].append(0)
        trim_list[i].append(0)
        trimrange_list[i].append(0)
        pass
    pass

if options.SaveFile:
    scanFits = fitScanData(filename+'.root')
    pass



for event in inF.scurveTree:
    strip = lookup_table[event.vfatN][event.vfatCH]
    if not options.channels:
        vSum[event.vfatN].Fill(strip,event.vcal,event.Nhits)
        pass
    else:
        vSum[event.vfatN].Fill(event.vfatCH,event.vcal,event.Nhits)
        pass
    vScurves[event.vfatN][event.vfatCH].Fill(event.vcal, event.Nhits)
    vthr_list[event.vfatN][event.vfatCH] = event.vthr
    trim_list[event.vfatN][event.vfatCH] = event.trimDAC
    trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
    pass
if options.SaveFile:
    for vfat in range (0,24):
        for CH in range (0, 128):
            strip = lookup_table[vfat][CH]
            #Filling the Branches
            param0 = scanFits[0][vfat][CH]
            param1 = scanFits[1][vfat][CH]
            param2 = scanFits[2][vfat][CH]
            FittedFunction =  TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
            FittedFunction.SetParameter(0, param0)
            FittedFunction.SetParameter(1, param1)
            FittedFunction.SetParameter(2, param2)
            ped_eff[0] = FittedFunction.Eval(0.0)
            vfatN[0] = vfat
            vfatCH[0] = CH
            vfatstrip[0] = strip
            trimRange[0] = trimrange_list[vfat][CH] 
            vthr[0] = vthr_list[vfat][CH]
            trimDAC[0] = trim_list[vfat][CH]
            threshold[0] = param0
            noise[0] = param1
            pedestal[0] = param2
            chi2[0] = scanFits[3][vfat][CH]
            holder_curve = vScurves[vfat][CH]
            holder_curve.Copy(scurve_h)
        #Filling the arrays for plotting later
            if options.drawbad:
                if (Chi2 > 1000.0 or Chi2 < 1.0):
                    overlay_fit(vfat, CH)
                    print "Chi2 is, %d"%(Chi2)
                    pass
                pass
            myT.Fill()
            pass 
        pass
    pass

canv = TCanvas('canv','canv',500*8,500*3)
canv.Divide(8,3)
for i in range(0,24):
    canv.cd(i+1)
    vSum[i].Draw('colz')
    canv.Update()
    pass
canv.SaveAs(filename+'/Summary.png')

if options.SaveFile:
    outF.cd()
    myT.Write()
    outF.Close()
    pass
