#!/bin/env python
import os
import sys
from optparse import OptionParser
from array import array
from fitScanData import *
from channelMaps import *
from PanChannelMaps import *
from gempython.utils.nesteddict import nesteddict as ndict

from qcoptions import parser

parser.add_option("-i", "--infilename", type="string", dest="filename", default="ThresholdData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename", default="ThresholdPlots.root",
                  help="Specify Output Filename", metavar="outfilename")
parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                  help="Specify GEB (long/short)", metavar="GEBtype")
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")
parser.add_option("-p","--panasonic", action="store_true", dest="PanPin",
                  help="Make plots vs Panasonic pins instead of strips", metavar="PanPin")
parser.add_option("--chConfigKnown", action="store_true", dest="chConfigKnown",
                  help="Channel config already known and found in --fileScurveFitTree", metavar="chConfigKnown")
parser.add_option("--fileScurveFitTree", type="string", dest="fileScurveFitTree", default="SCurveFitData.root",
                  help="TFile containing scurveFitTree", metavar="fileScurveFitTree")
parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                  help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename

vfat_mask = options.vfatmask

import ROOT as r
r.gROOT.SetBatch(True)
GEBtype = options.GEBtype
inF = r.TFile(filename+'.root')
outF = r.TFile(filename+'/'+outfilename, 'recreate')

VT1_MAX = 255

#Build the channel to strip mapping from the text file
lookup_table = []
pan_lookup = []
vfatCh_lookup = []
for vfat in range(0,24):
    lookup_table.append([])
    pan_lookup.append([])
    vfatCh_lookup.append([])
    for channel in range(0,128):
        lookup_table[vfat].append(0)
        pan_lookup[vfat].append(0)
        vfatCh_lookup[vfat].append(0)
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
    
    if not (options.channels or options.PanPin):     #Readout Strips
        vfatCh_lookup[int(mapping[0])][int(mapping[1])]=int(mapping[2]) - 1
        pass
    elif options.channels:                #VFAT Channels
        vfatCh_lookup[int(mapping[0])][int(mapping[2]) -1]=int(mapping[2]) - 1
        pass
    elif options.PanPin:                #Panasonic Connector Pins
        vfatCh_lookup[int(mapping[0])][int(mapping[3])]=int(mapping[2]) - 1
        pass
    pass

print 'Initializing Histograms'
vSum = ndict()
hot_channels = []
for vfat in range(0,24):
    hot_channels.append([])
    if not (options.channels or options.PanPin):
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'vSum%i;Strip;VThreshold1 [DAC units]'%vfat,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    elif options.channels:
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'vSum%i;Channel;VThreshold1 [DAC units]'%vfat,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    elif options.PanPin:
        vSum[vfat] = r.TH2D('vSum%i'%vfat,'vSum%i;Panasonic Pin;VThreshold1 [DAC units]'%vfat,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    for chan in range(0,128):
        hot_channels[vfat].append(False)
        pass
    pass

print 'Filling Histograms'
trimRange = {}
for event in inF.thrTree :
    if (vfat_mask >> int(event.vfatN)) & 0x1: continue

    strip = lookup_table[event.vfatN][event.vfatCH]
    pan_pin = pan_lookup[event.vfatN][event.vfatCH]
    trimRange[int(event.vfatN)] = int(event.trimRange)

    if options.channels:
        vSum[event.vfatN].Fill(event.vfatCH,event.vth1,event.Nhits)
        pass
    elif options.PanPin:
        vSum[event.vfatN].Fill(pan_pin,event.vth1,event.Nhits)
        pass
    else:
        vSum[event.vfatN].Fill(strip,event.vth1,event.Nhits)
        pass
    pass

#Determine Hot Channels
print 'Determining hot channels'
from qcutilities import *
import numpy as np
import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
dict_hMaxVT1 = {}
dict_hMaxVT1_NoOutlier = {}
for vfat in range(0,24):
    if (vfat_mask >> vfat) & 0x1: continue

    dict_hMaxVT1[vfat]          = r.TH1F('vfat%iChanMaxVT1'%vfat,"vfat%i"%vfat,256,-0.5,255.5)
    dict_hMaxVT1_NoOutlier[vfat]= r.TH1F('vfat%iChanMaxVT1_NoOutlier'%vfat,"vfat%i - No Outliers"%vfat,256,-0.5,255.5)

    #For each channel determine the maximum thresholds
    chanMaxVT1 = np.zeros((2,vSum[vfat].GetNbinsX()))
    for chan in range(0,vSum[vfat].GetNbinsX()):
        for thresh in range(vSum[vfat].ProjectionY("projY",chan,chan,"").GetMaximumBin(),VT1_MAX+1):
            if(vSum[vfat].ProjectionY("projY",chan,chan,"").GetBinContent(thresh) == 0):
                chanMaxVT1[0][chan]=chan
                chanMaxVT1[1][chan]=(thresh-1)
                dict_hMaxVT1[vfat].Fill(thresh-1)
                break
            pass
        pass

    #Determine Outliers (e.g. "hot" channels)
    chanOutliers = isOutlierMADOneSided(chanMaxVT1[1,:], thresh=options.zscore)
    for chan in range(0,len(chanOutliers)):
        hot_channels[vfat][chan] = chanOutliers[chan]
        
        if not chanOutliers[chan]:
            dict_hMaxVT1_NoOutlier[vfat].Fill(chanMaxVT1[1][chan])
            pass
        pass

    if options.debug:
        print "VFAT%i Max Thresholds By Channel"%vfat
        print chanMaxVT1

        print "VFAT%i Channel Outliers"%vfat
        chanOutliers = np.column_stack((chanMaxVT1[0,:],np.array(hot_channels[vfat]).astype(float)))
        print chanOutliers
        pass
    pass

# Fetch trimDAC & chMask from scurveFitTree
dict_vfatTrimMaskData = {}
if options.chConfigKnown:
    list_bNames = ["vfatN"]
    if not (options.channels or options.PanPin):
        list_bNames.append("ROBstr")
        pass
    elif options.channels:
        list_bNames.append("vfatCh")
        pass
    elif options.PanPin:
        list_bNames.append("panPin")
        pass
    list_bNames.append("mask")
    list_bNames.append("trimDAC")

    try:
        array_VFATSCurveData = rp.root2array(options.fileScurveFitTree,treename="scurveFitTree",branches=list_bNames)

        #pyVersion = 1. * sys.version_info[0] + 0.1 *sys.version_info[1]

        ##Initialize (key, value) pairing for dict_vfatTrimMaskData
        #if pyVersion >= 2.7:
        #    dict_vfatTrimMaskData = {idx:initVFATArray(array_VFATSCurveData.dtype) for idx in np.unique(array_VFATSCurveData[list_bNames[0]])}
        #    pass
        #else:
        #    dict_vfatTrimMaskData = dict((idx,initVFATArray(array_VFATSCurveData.dtype)) for idx in np.unique(array_VFATSCurveData[list_bNames[0]]))
        #    pass

        #Store array_VFATSCurveData into a dict for easy access
        #This dictionary has VFAT position as the key value, returns a structured numpy array
        #dict_vfatTrimMaskData = {idx:initVFATArray(array_VFATSCurveData.dtype) for idx in np.unique(array_VFATSCurveData[list_bNames[0]])}
        dict_vfatTrimMaskData = dict((idx,initVFATArray(array_VFATSCurveData.dtype)) for idx in np.unique(array_VFATSCurveData[list_bNames[0]]))
        for dataPt in array_VFATSCurveData:
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['mask'] =  dataPt['mask']
            dict_vfatTrimMaskData[dataPt['vfatN']][dataPt[list_bNames[1]]]['trimDAC'] =  dataPt['trimDAC']
            pass
        pass
    except Exception as e:
        print '%s does not seem to exist'%options.fileScurveFitTree
        print e
        pass
    pass

#Save Output
outF.cd()
canv = r.TCanvas('canv','canv',500*8,500*3)
canv.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for vfat in range(0,24):
    r.gStyle.SetOptStat(0)
    canv.cd(vfat+1)
    vSum[vfat].Draw('colz')
    vSum[vfat].Write()
    pass
canv.SaveAs(filename+'/ThreshSummary.png')

canv_proj = r.TCanvas('canv_proj', 'canv_proj', 500*8, 500*3)
canv_proj.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for vfat in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_proj.cd(vfat+1)
    r.gPad.SetLogy()
    vSum[vfat].ProjectionY().Draw()
    pass
canv_proj.SaveAs(filename+'/VFATSummary.png')

#Save VT1Max Distributions Before/After Outlier Rejection
canv_vt1Max = r.TCanvas('canv_vt1Max','canv_vt1Max', 500*8, 500*3)
canv_vt1Max.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving vt1Max distributions'
for vfat in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_vt1Max.cd(vfat+1)
    dict_hMaxVT1[vfat].Draw("hist")
    dict_hMaxVT1_NoOutlier[vfat].SetLineColor(r.kRed)
    dict_hMaxVT1_NoOutlier[vfat].Draw("samehist")
    pass
canv_vt1Max.SaveAs(filename+'/VT1MaxSummary.png')

#Subtracting off the hot channels, so the projection shows only usable ones.
print "Subtracting off hot channels"
for vfat in range(0,24):
    if (vfat_mask >> vfat) & 0x1: continue
    for chan in range(0,vSum[vfat].GetNbinsX()):
        isHotChan = hot_channels[vfat][chan]
       
        if options.chConfigKnown:
            isHotChan = (isHotChan or dict_vfatTrimMaskData[vfat][chan]['mask'])
            pass

        if isHotChan:
            print 'VFAT %i Strip %i is noisy'%(vfat,chan)
            for thresh in range(VT1_MAX+1):
                vSum[vfat].SetBinContent(chan, thresh, 0)
                pass
            pass
        pass
    pass

#Save output with new hot channels subtracted off
canv_pruned = r.TCanvas('canv_pruned','canv_pruned',500*8,500*3)
canv_pruned.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for vfat in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_pruned.cd(vfat+1)
    vSum[vfat].Draw('colz')
    vSum[vfat].Write()
    pass
canv_pruned.SaveAs(filename+'/ThreshPrunedSummary.png')

canv_proj = r.TCanvas('canv_proj_pruned', 'canv_proj_pruned', 500*8, 500*3)
canv_proj.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for vfat in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_proj.cd(vfat+1)
    r.gPad.SetLogy()
    vSum[vfat].ProjectionY().Draw()
    vSum[vfat].ProjectionY().Write()
    pass
canv_proj.SaveAs(filename+'/VFATPrunedSummary.png')
#outF.Close()

#Now determine what VT1 to use for configuration.  The first threshold bin with no entries for now.
#Make a text file readable by TTree::ReadFile
vt1 = {}
for vfat in range(0,24):
    if (vfat_mask >> vfat) & 0x1: continue
    for thresh in range(VT1_MAX+1,0,-1):
        if (vSum[vfat].ProjectionY().GetBinContent(thresh+1)) > 10.0:
            print 'vt1 for VFAT %i found'%vfat
            vt1[vfat]=(thresh+1)
            break
        pass
    pass
outF.Close()
txt_vfat = open(filename+"/vfatConfig.txt", 'w')

print "trimRange:"
print trimRange
print "vt1:"
print vt1

txt_vfat.write("vfatN/I:vt1/I:trimRange/I\n")
for vfat in range(0,24):
    if (vfat_mask >> vfat) & 0x1: continue
    txt_vfat.write('%i\t%i\t%i\n'%(vfat, vt1[vfat],trimRange[vfat]))
    pass
txt_vfat.close()

#Update channel registers configuration file
if options.chConfigKnown:
    confF = open(filename+'/chConfig_MasksUpdated.txt','w')
    confF.write('vfatN/I:vfatCH/I:trimDAC/I:mask/I\n')

    if options.debug:
        print 'vfatN/I:vfatCH/I:trimDAC/I:mask/I\n'
        pass

    for vfat in range (0,24):
        if (vfat_mask >> vfat) & 0x1: continue
        for j in range (0, 128):
            chan = vfatCh_lookup[vfat][j]
            if options.debug:
                print '%i\t%i\t%i\t%i\n'%(vfat,chan,dict_vfatTrimMaskData[vfat][j]['trimDAC'],int(hot_channels[vfat][j] or dict_vfatTrimMaskData[vfat][j]['mask']))
                pass

            confF.write('%i\t%i\t%i\t%i\n'%(vfat,chan,dict_vfatTrimMaskData[vfat][j]['trimDAC'],int(hot_channels[vfat][j] or dict_vfatTrimMaskData[vfat][j]['mask'])))
            pass
        pass

    confF.close()
    pass

print 'Analysis Completed Successfully'
