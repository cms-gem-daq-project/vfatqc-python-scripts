from ROOT import TFile,TTree,TH1D,TCanvas,gROOT,gStyle,TF1
import numpy as np

def fitScanData(treeFile):
    gROOT.SetBatch(True)
    gStyle.SetOptStat(0)

    inF = TFile(treeFile)

    scanHistos = {}
    scanFits = {}
    scanFits[0] = {}
    scanFits[1] = {}

    for vfat in range(0,24):
        scanHistos[vfat] = {}
        scanFits[0][vfat] = np.zeros(128)
        scanFits[1][vfat] = np.zeros(128)
        for ch in range(0,128):
            scanHistos[vfat][ch] = TH1D('scurve_%i_%i_h'%(vfat,ch),'scurve_%i_%i_h'%(vfat,ch),254,0.5,254.5)

    for event in inF.scurveTree :
        scanHistos[event.vfatN][event.vfatCH].Fill(event.vcal,event.Nhits)

    fitTF1 = TF1('myERF','500*TMath::Erf((x-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    for vfat in range(0,24):
        print 'fitting vfat %i'%vfat
        for ch in range(0,128):
            fitStatus = 1
            fitN = 0
            while(fitStatus):
                fitTF1.SetParameter(0,125.0)
                fitTF1.SetParameter(1,125.0+fitN*5.0)
                fitTF1.SetParLimits(0, 0.01, 300.0)
                fitResult = scanHistos[vfat][ch].Fit('myERF','S')
                fitStatus = fitResult.Status()
                scanFits[0][vfat][ch] = fitTF1.GetParameter(0)
                scanFits[1][vfat][ch] = fitTF1.GetParameter(1)
                fitN += 1

    return scanFits

