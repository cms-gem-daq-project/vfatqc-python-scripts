from ROOT import TFile,TTree,TH2D

inF = TFile('ThresholdData.root')

vSum = {}
for i in range(0,24):
    vSum[i] = TH2D('vSum%i'%i,'vSum%i;Channel;VThreshold1 [DAC units]'%i,128,-0.5,127.5,81,-0.5,80.5)

print 'Filling Histograms'
for event in inF.thrTree :
    vSum[event.vfatN].Fill(event.vfatCH,event.vth,event.Nhits)

outF = TFile('ThresholdPlots.root','recreate')
outF.cd()

print 'Saving File'
for i in range(0,24):
    vSum[i].Write()
outF.Close()
