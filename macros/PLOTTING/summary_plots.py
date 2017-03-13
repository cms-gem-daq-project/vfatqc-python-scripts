import os
from optparse import OptionParser
from ROOT import TFile,TTree,TH2D,TH1D,TGraph,TGraph2D,TCanvas,TPad,gROOT,gStyle,gPad,TPaveStats

parser = OptionParser()

parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveFitData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                  help="Specify GEB (long/short)", metavar="GEBtype")
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")
parser.add_option("-a","--all", action="store_true", dest="all_plots",
                  help="Make all plots", metavar="all_plots")
parser.add_option("-f","--fit", action="store_true", dest="fit_plots",
                  help="Make fit parameter plots", metavar="fit_plots")
parser.add_option("-x","--chi2", action="store_true", dest="chi2_plots",
                  help="Make Chi2 plots", metavar="chi2_plots")


(options, args) = parser.parse_args()
filename = options.filename[:-5]

gROOT.SetBatch(True)
GEBtype = options.GEBtype
inF = TFile(filename+'.root')

#Build the channel to strip mapping from the text file
lookup_table = []
for vfat in range(0,24):
    lookup_table.append([])
    for channel in range(0,128):
        lookup_table[vfat].append(0)
        pass
    pass

buildHome = os.environ.get('BUILD_HOME')

if GEBtype == 'long':
    intext = open(buildHome+'/vfatqc-python-scripts/macros/longChannelMap.txt', 'r')
    for i, line in enumerate(intext):
        if i == 0: continue
        mapping = line.rsplit('\t')
        lookup_table[int(mapping[0])][int(mapping[2]) -1] = int(mapping[1])
        pass
    pass
if GEBtype == 'short':
    intext = open(buildHome+'/vfatqc-python-scripts/macros/shortChannelMap.txt', 'r')
    for i, line in enumerate(intext):
        if i == 0: continue
        mapping = line.rsplit('\t')
        lookup_table[int(mapping[0])][int(mapping[2]) -1] = int(mapping[1])
        pass
    pass


vSum = {}
vNoise = {}
vThreshold = {}
vChi2 = {}
vComparison = {}
vPedestal = {}


for i in range(0,24):
    vNoise[i] = TH1D('Noise%i'%i,'Noise%i;Noise [DAC units]'%i,35,-0.5,34.5)
    vPedestal[i] = TH1D('Pedestal%i'%i,'Pedestal%i;Pedestal [DAC units]'%i,256,-0.5,255.5)
    vThreshold[i] = TH1D('Threshold%i'%i,'Threshold%i;Threshold [DAC units]'%i,60,-0.5,299.5)
    vChi2[i] = TH1D('ChiSquared%i'%i,'ChiSquared%i;Chi2'%i,100,-0.5,999.5)
    vComparison[i] = TH2D('vComparison%i'%i,'Parameter Spread %i;Threshold [DAC units];Noise [DAC units]'%i,60,-0.5,299.5,70,-0.5,34.5)
    pass

for event in inF.scurveFitTree:
    strip = lookup_table[event.vfatN][event.vfatCH]
    param0 = event.threshold
    param1 = event.noise
    param2 = event.pedestal
    vThreshold[event.vfatN].Fill(param0)
    vNoise[event.vfatN].Fill(param1)
    vPedestal[event.vfatN].Fill(param2)
    vChi2[event.vfatN].Fill(event.chi2)
    vComparison[event.vfatN].Fill(param0, param1)
    pass
    
if options.fit_plots or options.all_plots:
    gStyle.SetOptStat(111100)
    canv_comp = TCanvas('canv_comp','canv_comp',500*8,500*3)
    canv_comp.Divide(8,3)
    for i in range(0,24):
        canv_comp.cd(i+1)
        gStyle.SetOptStat(111100)
        vComparison[i].Draw('colz')
        canv_comp.Update()
        pass
    canv_comp.SaveAs(filename+'_ParameterSpread.png')
    
    canv_thresh = TCanvas('canv_thresh','canv_thresh',500*8,500*3)
    canv_thresh.Divide(8,3)
    for i in range(0,24):
        canv_thresh.cd(i+1)
        gStyle.SetOptStat(111100)
        vThreshold[i].Draw()
        gPad.SetLogy()
        canv_thresh.Update()
        pass
    canv_thresh.SaveAs(filename+'_FitThreshSummary.png')
    
    canv_Pedestal = TCanvas('canv_Pedestal','canv_Pedestal',500*8,500*3)
    canv_Pedestal.Divide(8,3)
    for i in range(0,24):
        canv_Pedestal.cd(i+1)
        gStyle.SetOptStat(111100)
        vPedestal[i].Draw()
        gPad.SetLogy()
        canv_Pedestal.Update()
        pass
    canv_Pedestal.SaveAs(filename+'_FitPedestalSummary.png')
    
    canv_noise = TCanvas('canv_noise','canv_noise',500*8,500*3)
    canv_noise.Divide(8,3)
    for i in range(0,24):
        canv_noise.cd(i+1)
        vNoise[i].Draw()
        gPad.SetLogy()
        canv_noise.Update()
        pass
    canv_noise.SetLogy()
    canv_noise.SaveAs(filename+'_FitNoiseSummary.png')
    pass
if options.chi2_plots or options.all_plots:    
    canv_Chi2 = TCanvas('canv_Chi2','canv_Chi2',500*8,500*3)
    canv_Chi2.Divide(8,3)
    canv_Chi2.SetLogy()
    for i in range(0,24):
        canv_Chi2.cd(i+1)
        vChi2[i].Draw()
        gPad.SetLogy()
        canv_Chi2.Update()
        pass
    canv_Chi2.SetLogy()
    canv_Chi2.SaveAs(filename+'_FitChi2Summary.png')
    pass

