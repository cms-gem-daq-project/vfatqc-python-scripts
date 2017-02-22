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
    scanFits[2] = {}
    scanFits[3] = {}
    scanFits[4] = {}

    for vfat in range(0,24):
        scanHistos[vfat] = {}
        scanFits[0][vfat] = np.zeros(128)
        scanFits[1][vfat] = np.zeros(128)
        scanFits[2][vfat] = np.zeros(128)
        for ch in range(0,128):
            scanHistos[vfat][ch] = TH1D('scurve_%i_%i_h'%(vfat,ch),'scurve_%i_%i_h'%(vfat,ch),254,0.5,254.5)

    for event in inF.scurveTree :
        scanHistos[event.vfatN][event.vfatCH].Fill(event.vcal,event.Nhits)
        scanFits[3][event.vfat][event.ch] = fitTF1.GetChisquare()
        scanFits[4][event.vfat][event.ch] = fitTF1.GetChisquare()

    fitTF1 = TF1('myERF','500*TMath::Erf((x-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    for vfat in range(0,24):
        print 'fitting vfat %i'%vfat
        for ch in range(0,128):
            fitStatus = 1
            fitChi2 = 0
            fitN = 0
            tryN = 0
            while(fitStatus or fitChi2 > 10000.0):
                fitTF1.SetParameter(0,125.0)
                fitTF1.SetParameter(1,125.0+fitN*5.0)
                fitTF1.SetParLimits(0, 0.01, 300.0)
                fitResult = scanHistos[vfat][ch].Fit('myERF','S')
                fitStatus = fitResult.Status()
                fitChi2 = fitResult.Chi2()
                print fitChi2
                scanFits[0][vfat][ch] = fitTF1.GetParameter(0)
                scanFits[1][vfat][ch] = fitTF1.GetParameter(1)
                scanFits[2][vfat][ch] = fitTF1.GetChisquare()
                fitN += 1
                if(tryN > 25): break
                tryN += 1

    return scanFits

