from ROOT import TFile,TTree,TH2D,TCanvas,TPad,gROOT,gStyle

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

inF = TFile('testName.root')

vSum = {}
for i in range(0,24):
    vSum[i] = TH2D('vSum%i'%i,'vSum%i;Channel;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)

for event in inF.scurveTree :
    vSum[event.vfatN].Fill(event.vfatCH,event.vcal,event.Nhits)

outF = TFile('SCurvePlots.root','recreate')
outF.cd()

canv = TCanvas('canv','canv',500*8,500*3)
canv.Divide(8,3)
for i in range(0,24):
    canv.cd(i+1)
    vSum[i].Draw('colz')
    canv.Update()
    vSum[i].Write()
canv.SaveAs('SCurveSummary.png')
outF.Close()
