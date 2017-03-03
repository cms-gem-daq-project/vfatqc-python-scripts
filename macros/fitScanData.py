from ROOT import TFile,TTree,TH1D,TCanvas,gROOT,gStyle,TF1, TRandom3
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

    for vfat in range(0,24):
        scanHistos[vfat] = {}
        scanFits[0][vfat] = np.zeros(128)
        scanFits[1][vfat] = np.zeros(128)
        scanFits[2][vfat] = np.zeros(128)
        for ch in range(0,128):
            scanHistos[vfat][ch] = TH1D('scurve_%i_%i_h'%(vfat,ch),'scurve_%i_%i_h'%(vfat,ch),254,0.5,254.5)

    for event in inF.scurveTree :
        scanHistos[event.vfatN][event.vfatCH].Fill(event.vcal,event.Nhits)
        pass
    random = TRandom3()
    random.SetSeed(0)
    fitTF1 = TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    for vfat in range(0,24):
        print 'fitting vfat %i'%vfat
        for ch in range(0,128):
            fitStatus = 1
            fitChi2 = 0
            fitN = 0
            fitGoodN = 0
            MinChi2Temp = 99999999
            stepN = 0
            while(stepN < 25):
                rand = random.Gaus(10, 5)
                if (rand < 0.0 or rand > 100): continue
                fitTF1.SetParameter(0, 8+stepN*8)
                fitTF1.SetParameter(1,rand)
                fitTF1.SetParameter(2,8+stepN)
                fitTF1.SetParLimits(0, 0.01, 300.0)
                fitTF1.SetParLimits(1, 0.0, 100.0)
                fitTF1.SetParLimits(2, 0.0, 300.0)
                fitResult = scanHistos[vfat][ch].Fit('myERF','S')
                fitStatus = fitResult.Status()
                fitChi2 = fitResult.Chi2()
                print fitChi2
                Chi2Temp = fitChi2
                stepN +=1
                fitGoodN+=1
                if (Chi2Temp < MinChi2Temp):
                    scanFits[0][vfat][ch] = fitTF1.GetParameter(0)
                    scanFits[1][vfat][ch] = fitTF1.GetParameter(1)
                    scanFits[2][vfat][ch] = fitChi2
                    MinChi2Temp = Chi2Temp
                    pass
                if (MinChi2Temp < 50): break
                pass
            pass
        pass
    return scanFits
