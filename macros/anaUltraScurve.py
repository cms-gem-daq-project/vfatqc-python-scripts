#!/bin/env python
import os
from optparse import OptionParser
from array import array
from fitScanData import *
from channelMaps import *
from PanChannelMaps import *
from gempython.utils.nesteddict import nesteddict as ndict

parser = OptionParser()

parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename", default="SCurveFitData.root",
                  help="Specify Output Filename", metavar="outfilename")
parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                  help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                  help="Specify GEB (long/short)", metavar="GEBtype")
parser.add_option("-f", "--fit", action="store_true", dest="SaveFile",
                  help="Save the Fit values to Root file", metavar="SaveFile")
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")
parser.add_option("-p","--panasonic", action="store_true", dest="PanPin",
                  help="Make plots vs Panasonic pins instead of strips", metavar="PanPin")
parser.add_option("--IsTrimmed", action="store_true", dest="IsTrimmed",
                  help="If the data is from a trimmed scan, plot the value it tried aligning to", metavar="IsTrimmed")


(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename

import ROOT as r

r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(1111111)
GEBtype = options.GEBtype
inF = r.TFile(filename+'.root')

if options.SaveFile:
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    myT = r.TTree('scurveFitTree','Tree Holding FitData')
    pass
#Build the channel to strip mapping from the text file
lookup_table = []
pan_lookup = []
for vfat in range(0,24):
    lookup_table.append([])
    pan_lookup.append([])
    for channel in range(0,128):
        lookup_table[vfat].append(0)
        pan_lookup[vfat].append(0)
        pass
    pass

buildHome = os.environ.get('BUILD_HOME')

if GEBtype == 'long':
    intext = open(buildHome+'/vfatqc-python-scripts/macros/longChannelMap.txt', 'r')
    pass
if GEBtype == 'short':
        intext = open(buildHome+'/vfatqc-python-scripts/macros/shortChannelMap.txt', 'r')
        pass
for i, line in enumerate(intext):
    if i == 0: continue
    mapping = line.rsplit('\t')
    lookup_table[int(mapping[0])][int(mapping[2]) -1] = int(mapping[1])
    pan_lookup[int(mapping[0])][int(mapping[2]) -1] = int(mapping[3])
    pass

if options.IsTrimmed:
    trimmed_text = open('scanInfo.txt', 'r')
    trimVcal = []
    for vfat in range(0,24):
        trimVcal.append(0)
        pass
    for n, line in enumerate(trimmed_text):
        if n == 0: continue
        print line
        scanInfo = line.rsplit('  ')
        trimVcal[int(scanInfo[0])] = float(scanInfo[4])
        pass
    pass

if options.SaveFile:
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    ROBstr = array( 'i', [ 0 ] )
    myT.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
    mask = array( 'i', [ 0 ] )
    myT.Branch( 'mask', mask, 'mask/I' )
    panPin = array( 'i', [ 0 ] )
    myT.Branch( 'panPin', panPin, 'panPin/I' )
    trimRange = array( 'i', [ 0 ] )
    myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
    vthr = array( 'i', [ 0 ] )
    myT.Branch( 'vthr', vthr, 'vthr/I' )
    trimDAC = array( 'i', [ 0 ] )
    myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
    threshold = array( 'f', [ 0 ] )
    myT.Branch( 'threshold', threshold, 'threshold/F')
    noise = array( 'f', [ 0 ] )
    myT.Branch( 'noise', noise, 'noise/F')
    pedestal = array( 'f', [ 0 ] )
    myT.Branch( 'pedestal', pedestal, 'pedestal/F')
    ped_eff = array( 'f', [ 0 ] )
    myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
    scurve_h = r.TH1D()
    myT.Branch( 'scurve_h', scurve_h)
    chi2 = array( 'f', [ 0 ] )
    myT.Branch( 'chi2', chi2, 'chi2/F')
    Nev = array( 'f', [ 0 ] )
    myT.Branch( 'Nev', Nev, 'Nev/F')
    pass

vSum  = ndict()
vSum2 = ndict()
vScurves = []
vthr_list = []
trim_list = []
trimrange_list = []
lines = []
def overlay_fit(VFAT, CH):
    Scurve = r.TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CH),255,-0.5,254.5)
    strip = lookup_table[VFAT][CH]
    pan_pin = pan_lookup[VFAT][CH]
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CH):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    param0 = scanFits[0][VFAT][CH]
    param1 = scanFits[1][VFAT][CH]
    param2 = scanFits[2][VFAT][CH]
    fitTF1 =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    fitTF1.SetParameter(2, param2)
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(1111111)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, strip))
    return



for i in range(0,24):
    vScurves.append([])
    vthr_list.append([])
    trim_list.append([])
    trimrange_list.append([])
    if options.IsTrimmed:
        lines.append(r.TLine(-0.5, trimVcal[i], 127.5, trimVcal[i]))
        pass
    if not (options.channels or options.PanPin):
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i;Strip;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
        vSum[i].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.channels:
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i;Channels;VCal [DAC units]'%i,128,-0.5,127.5,256,-0.5,255.5)
        vSum[i].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.PanPin:
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i_0-63;63 - Panasonic Pin;VCal [DAC units]'%i,64,-0.5,63.5,256,-0.5,255.5)
        vSum[i].GetYaxis().SetTitleOffset(1.5)
        vSum2[i] = r.TH2D('vSum2_%i'%i,'vSum%i_64-127;127 - Panasonic Pin;VCal [DAC units]'%i,64,-0.5,63.5,256,-0.5,255.5)
        vSum2[i].GetYaxis().SetTitleOffset(1.5)
        pass
    for ch in range (0,128):
        vScurves[i].append(r.TH1D('Scurve_%i_%i'%(i,ch),'Scurve_%i_%i;VCal [DAC units]'%(i,ch),256,-0.5,255.5))
        vthr_list[i].append(0)
        trim_list[i].append(0)
        trimrange_list[i].append(0)
        pass
    pass

if options.SaveFile:
    scanFits = fitScanData(filename+'.root')
    pass



for event in inF.scurveTree:
    strip = lookup_table[event.vfatN][event.vfatCH]
    pan_pin = pan_lookup[event.vfatN][event.vfatCH]
    if not (options.channels or options.PanPin):
        vSum[event.vfatN].Fill(strip,event.vcal,event.Nhits)
        pass
    if options.channels:
        vSum[event.vfatN].Fill(event.vfatCH,event.vcal,event.Nhits)
        pass
    if options.PanPin:
        if (pan_pin < 64):
            vSum[event.vfatN].Fill(63-pan_pin,event.vcal,event.Nhits)
            pass
        else:
            vSum2[event.vfatN].Fill(127-pan_pin,event.vcal,event.Nhits)
            pass
        pass
    x = vScurves[event.vfatN][event.vfatCH].FindBin(event.vcal)
    vScurves[event.vfatN][event.vfatCH].SetBinContent(x, event.Nhits)
    r.gStyle.SetOptStat(1111111)
    vthr_list[event.vfatN][event.vfatCH] = event.vthr
    trim_list[event.vfatN][event.vfatCH] = event.trimDAC
    trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
    pass
if options.SaveFile:
    masks = []
    for vfat in range (0,24):
        masks.append([])
        for ch in range (0, 128):
            strip = lookup_table[vfat][ch]
            pan_pin = pan_lookup[vfat][ch]
            #Filling the Branches
            param0 = scanFits[0][vfat][ch]
            param1 = scanFits[1][vfat][ch]
            param2 = scanFits[2][vfat][ch]
            FittedFunction =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
            FittedFunction.SetParameter(0, param0)
            FittedFunction.SetParameter(1, param1)
            FittedFunction.SetParameter(2, param2)
            ped_eff[0] = FittedFunction.Eval(0.0)
            vfatN[0] = vfat
            vfatCH[0] = ch
            ROBstr[0] = strip
            panPin[0] = pan_pin
            trimRange[0] = trimrange_list[vfat][ch] 
            vthr[0] = vthr_list[vfat][ch]
            trimDAC[0] = trim_list[vfat][ch]
            threshold[0] = param0
            noise[0] = param1
            pedestal[0] = param2
            if noise[0] > 20.0 or ped_eff[0] > 50.0: mask[0] = True
            else: mask[0] = False
            masks[vfat].append(mask[0])
            chi2[0] = scanFits[3][vfat][ch]
            holder_curve = vScurves[vfat][ch]
            holder_curve.Copy(scurve_h)
            Nev[0] = scanFits[4][vfat][ch]
        #Filling the arrays for plotting later
            if options.drawbad:
                if (Chi2 > 1000.0 or Chi2 < 1.0):
                    overlay_fit(vfat, ch)
                    print "Chi2 is, %d"%(Chi2)
                    pass
                pass
            myT.Fill()
            pass 
        pass
    pass

canv = r.TCanvas('canv','canv',500*8,500*3)
legend = r.TLegend(0.75,0.7,0.88,0.88)
if not options.PanPin:
    canv.Divide(8,3)
    r.gStyle.SetOptStat(0)
    for i in range(0,24):
        r.gStyle.SetOptStat(0)
        canv.cd(i+1)
        vSum[i].Draw('colz')
        if options.IsTrimmed:
            legend.Clear()
            legend.AddEntry(line, 'trimVCal is %f'%(trimVcal[i]))
            legend.Draw('SAME')
            print trimVcal[i]
            lines[i].SetLineColor(1)
            lines[i].SetLineWidth(3)
            lines[i].Draw('SAME')
            pass
        canv.Update()
        pass
    pass
else:
    canv.Divide(8,6)
    r.gStyle.SetOptStat(0)
    for i in range(0,8):
        for j in range (0,3):
            r.gStyle.SetOptStat(0)
            canv.cd((i+1 + j*16)%48 + 16)
            vSum[i+(8*j)].Draw('colz')
            canv.Update()
            canv.cd((i+9 + j*16)%48 + 16)
            vSum2[i+(8*j)].Draw('colz')
            canv.Update()
            pass
        pass
    pass

canv.SaveAs(filename+'/Summary.png')

if options.SaveFile:
    confF = open(filename+'/chConfig.txt','w')
    confF.write('vfatN/I:vfatCH/I:trimDAC/I:mask/I\n')
    for vfat in range (0,24):
        for ch in range (0, 128):
            confF.write('%i\t%i\t%i\t%i\n'%(vfat,ch,trim_list[vfat][ch],masks[vfat][ch]))
            pass
        pass
    confF.close()
    outF.cd()
    myT.Write()
    outF.Close()
    pass

























