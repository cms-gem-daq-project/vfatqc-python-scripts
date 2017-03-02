from optparse import OptionParser
from array import array
from fitScanData import *
from ROOT import TFile,TTree,TH2D,TGraph,TGraph2D,TCanvas,TPad,gROOT,gStyle,gPad,TPaveStats



def overlay_fit(VFAT, CH, data_filename, fit_filename):
    inF = TFile(data_filename)
    fitF = TFile(fit_filename)
    Scurve = TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CH),255,-0.5,254.5)
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    for event in fitF.scurveFitTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            param0 = event.threshold
            param1 = event.noise
            pass
        pass
    fitTF1 =  TF1('myERF','500*TMath::Erf((x-[0])/(TMath::Sqrt(2)*[1]))+500',1, 253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    canvas = TCanvas('canvas', 'canvas', 500, 500)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Channel%i.png'%(VFAT, CH))
    return

overlay_fit(0, 2, 'SCurveData_trimdac0_range0.root', 'SCurveFitData.root')
