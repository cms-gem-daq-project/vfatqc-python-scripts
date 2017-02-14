from ROOT import TFile,TTree,TH1D,TCanvas,gROOT,gStyle,TF1

def fitScanData(treeFile):
    gROOT.SetBatch(True)
    gStyle.SetOptStat(0)

    inF = TFile(treeFile)

    scanHistos = {}
    scanFits = {}

    for vfat in range(0,24):
        scanHistos[vfat] = {}
        scanFits[vfat] = {}
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
                fitTF1.SetParameter(0,5*fitN)
                fitTF1.SetParameter(1,2.0)
                fitResult = scanHistos[vfat][ch].Fit('myERF','S')
                fitStatus = fitResult.Status()
                scanFits[vfat][ch] = fitTF1.GetParameter(0)
                fitN += 1

    return scanFits

