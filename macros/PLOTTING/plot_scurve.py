from optparse import OptionParser
from array import array
from ROOT import TFile,TTree,TH1D,TGraph,TGraph2D,TCanvas,TPad,gROOT,gStyle,gPad,TPaveStats,TF1

def plot_scurve(VFAT, CH, fit_filename, overlay_fit, channel_yes):
    fitF = TFile(fit_filename)
    Scurve = TH1D()
#    Scurve = TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CH),255,-0.5,254.5)
    for event in fitF.scurveFitTree:
        if (event.vfatN == VFAT) and ((event.vfatCH == CH and channel_yes) or (event.vfatstrip == CH and not channel_yes)):
            Scurve = ((fitF.scurveFitTree.scurve_h).Clone())
            if overlay_fit:
                param0 = event.threshold
                param1 = event.noise
                param2 = event.pedestal
                pass
            pass
        pass
    if overlay_fit:
        fitTF1 =  TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
        fitTF1.SetParameter(0, param0)
        fitTF1.SetParameter(1, param1)
        fitTF1.SetParameter(2, param2)
        pass
    canvas = TCanvas('canvas', 'canvas', 500, 500)
    gStyle.SetOptStat(0)
    Scurve.Draw()
    if overlay_fit:
        fitTF1.Draw('SAME')
        pass
    canvas.Update()
    if overlay_fit:
        gStyle.SetOptStat(111)
        print param0, param1, param2
        if channel_yes:
            canvas.SaveAs('Fit_Overlay_VFAT%i_Channel%i.png'%(VFAT, CH))
            pass
        else:
            canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, CH))
            pass
    else:
        if channel_yes:
            canvas.SaveAs('Scurve_VFAT%i_Channel%i.png'%(VFAT, CH))
            pass
        else:
            canvas.SaveAs('Scurve_VFAT%i_Strip%i.png'%(VFAT, CH))
            pass
        pass
    return

#overlay_fit(8, 106, 'SCurveData_Trimmed.root', 'SCurveFitData.root')
