from optparse import OptionParser
from array import array
from fitScanData import *
from ROOT import TFile,TTree,TH2D,TGraph,TGraph2D,TCanvas,TPad,gROOT,gStyle,gPad,TPaveStats

parser = OptionParser()

parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename", default="SCurveFitData.root",
                  help="Specify Output Filename", metavar="outfilename")
parser.add_option("-d", "--drawbad", action="store_true", dest="drawbad",
                  help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")


(options, args) = parser.parse_args()
filename = options.filename
print filename
outfilename = options.outfilename
gROOT.SetBatch(True)
#gStyle.SetOptStat(0)

inF = TFile(filename)

outF = TFile(outfilename, 'recreate')

myT = TTree('scurveFitTree','Tree Holding FitData')

vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatCH = array( 'i', [ 0 ] )
myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
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
chi2 = array( 'f', [ 0 ] )
myT.Branch( 'chi2', chi2, 'chi2/F')

scanFits = fitScanData(filename)
vSum = {}
vNoise = {}
vThreshold = {}
vChi2 = {}
vComparison = {}

def overlay_fit(VFAT, CH):
    Scurve = TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CH),255,-0.5,254.5)
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    param0 = scanFits[0][VFAT][CH]
    param1 = scanFits[1][VFAT][CH]

    fitTF1 =  TF1('myERF','500*TMath::Erf((x-[0])/(TMath::Sqrt(2)*[1]))+500',1, 253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    print param0, param1
    canvas = TCanvas('canvas', 'canvas', 500, 500)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Channel%i.png'%(VFAT, CH))
    return



for i in range(0,24):
    vSum[i] = TH2D('vSum%i'%i,'vSum%i;Channel;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
    vNoise[i] = TH1D('Noise%i'%i,'Noise%i;Noise'%i,35,-0.5,34.5)
    vThreshold[i] = TH1D('Threshold%i'%i,'Threshold%i;Threshold'%i,256,-0.5,255.5)
    vChi2[i] = TH1D('ChiSquared%i'%i,'ChiSquared%i;Chi2'%i,100,-0.5,999.5)
    vComparison[i] = TH2D('vComparison%i'%i,'Parameter Spread %i;Threshold;Noise'%i,256,-0.5,255.5,70,-0.5,34.5)
    pass

for event in inF.scurveTree:
    vSum[event.vfatN].Fill(event.vfatCH,event.vcal,event.Nhits)
    if event.vcal == 1:
        vfatN[0] = event.vfatN
        vfatCH[0] = event.vfatCH
        trimRange[0] = event.trimRange
        vthr[0] = event.vthr
        trimDAC[0] = event.trimDAC
        threshold[0] = scanFits[0][event.vfatN][event.vfatCH]
        noise[0] = scanFits[1][event.vfatN][event.vfatCH]
        chi2[0] = scanFits[2][event.vfatN][event.vfatCH]
        vNoise[event.vfatN].Fill((scanFits[1][event.vfatN][event.vfatCH]))
        vThreshold[event.vfatN].Fill((scanFits[0][event.vfatN][event.vfatCH]))
        vChi2[event.vfatN].Fill((scanFits[2][event.vfatN][event.vfatCH]))
        vComparison[event.vfatN].Fill(scanFits[0][event.vfatN][event.vfatCH], scanFits[1][event.vfatN][event.vfatCH])
        if (scanFits[2][event.vfatN][event.vfatCH] > 1000) and options.drawbad:
            overlay_fit(event.vfatN, event.vfatCH)
            pass
        myT.Fill()
        pass
    pass 

outF.cd()


canv = TCanvas('canv','canv',500*8,500*3)
canv.Divide(8,3)
for i in range(0,24):
    canv.cd(i+1)
    vSum[i].Draw('colz')
    canv.Update()
    vSum[i].Write()
    pass
canv.SaveAs(filename[:-5]+'.png')

gStyle.SetOptStat(111100)
canv_comp = TCanvas('canv','canv',500*8,500*3)
canv_comp.Divide(8,3)
for i in range(0,24):
    canv_comp.cd(i+1)
    gStyle.SetOptStat(111100)
    vComparison[i].Draw('colz')
    canv_comp.Update()
    vComparison[i].Write()
    pass
canv_comp.SaveAs('ParameterSpread.png')


canv_thresh = TCanvas('canv','canv',500*8,500*3)
canv_thresh.Divide(8,3)
for i in range(0,24):
    canv_thresh.cd(i+1)
    gStyle.SetOptStat(111100)
    vThreshold[i].Draw()
    gPad.SetLogy()
    canv_thresh.Update()
    vThreshold[i].Write()
    pass
canv_thresh.SaveAs('FitThreshSummary.png')

canv_noise = TCanvas('canv','canv',500*8,500*3)
canv_noise.Divide(8,3)
for i in range(0,24):
    canv_noise.cd(i+1)
    vNoise[i].Draw()
    gPad.SetLogy()
    canv_noise.Update()
    vNoise[i].Write()
    pass
canv_noise.SetLogy()
canv_noise.SaveAs('FitNoiseSummary.png')

canv_Chi2 = TCanvas('canv','canv',500*8,500*3)
canv_Chi2.Divide(8,3)
canv_Chi2.SetLogy()
for i in range(0,24):
    canv_Chi2.cd(i+1)
    vChi2[i].Draw()
    gPad.SetLogy()
    canv_Chi2.Update()
    vChi2[i].Write()
    pass
canv_Chi2.SetLogy()
canv_Chi2.SaveAs('FitChi2Summary.png')

outF.Write()
outF.Close()
