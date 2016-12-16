from ROOT import TFile,TTree,TH2D,TCanvas,TPad,gROOT,gStyle

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

inF = TFile('SCurveData.root')

vSum = {}
for i in range(0,24):
    vSum[i] = TH2D('vSum%i'%i,'vSum%i;Channel;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
print vSum

for event in inF.scurveTree :
    vSum[event.vfatN].Fill(event.vfatCH,event.vcal,event.Nhits)

outF = TFile('SCurvePlots.root','recreate')
outF.cd()

canv = TCanvas('canv','canv',500*8,500*3)
pads = {}
for i in range(0,24):
    pads[i] = TPad('pad%i'%i,'pad%i'%i,(i%8)/8.0+0.1/8,(i%3)/3.0+0.1/3,1-(i%8)/8.0-0.1/8,1-(i%3)/3.0-0.1/3)
for i in range(0,24):
    pads[i].Draw()
for i in range(0,24):
    pads[i].cd()
    vSum[i].Draw('colz')
    canv.Update()
    vSum[i].Write()
canv.SaveAs('ThresholdSummary.png')
outF.Close()
