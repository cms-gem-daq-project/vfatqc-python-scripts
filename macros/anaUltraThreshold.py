#!/bin/env python2.7
import os
from optparse import OptionParser
from array import array
from fitScanData import *
from channelMaps import *
from PanChannelMaps import *
from gempython.utils.nesteddict import nesteddict as ndict

from qcoptions import parser

#parser = OptionParser()
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

#VT1_MAX = 250
VT1_MAX = 255

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

vSum = ndict()
hot_channels = []
for i in range(0,24):
    hot_channels.append([])
    if not (options.channels or options.PanPin):
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i;Strip;VThreshold1 [DAC units]'%i,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    elif options.channels:
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i;Channel;VThreshold1 [DAC units]'%i,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    elif options.PanPin:
        vSum[i] = r.TH2D('vSum%i'%i,'vSum%i;Panasonic Pin;VThreshold1 [DAC units]'%i,128,-0.5,127.5,VT1_MAX+1,-0.5,VT1_MAX+0.5)
        pass
    for j in range(0,128):
        hot_channels[i].append(False)
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
        #if event.vth1 > 150 and event.Nhits > 0:
        #    hot_channels[event.vfatN][event.vfatCH] = True
        #    pass
        pass
    elif options.PanPin:
        vSum[event.vfatN].Fill(pan_pin,event.vth1,event.Nhits)
        #if event.vth1 > 150 and event.Nhits > 0:
        #    hot_channels[event.vfatN][pan_pin] = True
        #    pass
        pass
    else:
	#print str(event.vfatN)+"\t"+str(strip)+"\t"+str(event.vth1)+"\t"+str(event.Nhits) 
        vSum[event.vfatN].Fill(strip,event.vth1,event.Nhits)
        #if event.vth1 > 150 and event.Nhits > 0:
        #    hot_channels[event.vfatN][strip] = True
        #    pass
        pass

#Determine Hot Channels
print 'Determining hot channels'
from qcutilities import isOutlier
#import root_numpy as rp #note need root_numpy-4.7.2 (may need to run 'pip install root_numpy --upgrade')
import numpy as np
for i in range(0,24):
    if (vfat_mask >> i) & 0x1: continue
    #histData = rp.hist2array(vSum[i],include_overflow=False, return_edges=True)
#    histData = rp.hist2array(vSum[i], include_overflow=False, return_edges=False)
#    if i==0:
#	print "vSum[i].GetNbinsX() = " + str(vSum[i].GetNbinsX())
#        print "vSum[i].GetNbinsY() = " + str(vSum[i].GetNbinsY())
#	print "np.shape(histData) = " + str(np.shape(histData))
#	print "np.shape(histData[0,:]) = " + str(np.shape(histData[0,:]))
#	print histData[0,:]
#	pass

    #For each channel determine the maximum thresholds
    chanMaxVT1 = np.zeros((2,vSum[i].GetNbinsX()))
    for chan in range(0,vSum[i].GetNbinsX()):
	for j in range(VT1_MAX+1,0,-1):
	    if(vSum[i].ProjectionY("projY",chan,chan,"").GetBinContent(j+1) > 1.0):
		#print chan, j
		chanMaxVT1[0][chan]=chan
		chanMaxVT1[1][chan]=(j+1)
		break
	    pass
	pass

    #Determine Outliers (e.g. "hot" channels)
    chanOutliers = isOutlier(chanMaxVT1[1,:])
    for chan in range(0,len(chanOutliers)):
	hot_channels[i][chan] = chanOutliers[chan]
	pass

    if i==0:
	print "VFAT Max Thresholds By Channel"
	print chanMaxVT1
	print "VFAT Channel Outliers"
	#print hot_channels[i]

	chanOutliers = np.column_stack((chanMaxVT1[0,:],np.array(hot_channels[i]).astype(float)))
	print chanOutliers

	pass
    
    pass

outF.cd()
canv = r.TCanvas('canv','canv',500*8,500*3)
canv.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for i in range(0,24):
    r.gStyle.SetOptStat(0)
    canv.cd(i+1)
    vSum[i].Draw('colz')
    vSum[i].Write()
    pass
canv.SaveAs(filename+'/ThreshSummary.png')

canv_proj = r.TCanvas('canv_proj', 'canv_proj', 500*8, 500*3)
canv_proj.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for i in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_proj.cd(i+1)
    r.gPad.SetLogy()
    vSum[i].ProjectionY().Draw()
    #vSum[i].ProjectionY().Write()
    pass
canv_proj.SaveAs(filename+'/VFATSummary.png')

#Subtracting off the hot channels, so the projection shows only usable ones.
print "Subtracting off hot channels"
for i in range(0,24):
    if (vfat_mask >> i) & 0x1: continue
    for j in range(0,vSum[i].GetNbinsX()):
       if hot_channels[i][j]:
           print 'VFAT %i Strip %i is noisy'%(i,j)
           for binY in range(VT1_MAX+1):
               #bin = vSum[i].GetBin(j+1, binY)
               #content = vSum[i].GetBinContent(bin)
               vSum[i].SetBinContent(j, binY,0)
               pass
           pass
       pass
    pass

canv_pruned = r.TCanvas('canv_pruned','canv_pruned',500*8,500*3)
canv_pruned.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for i in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_pruned.cd(i+1)
    vSum[i].Draw('colz')
    vSum[i].Write()
    pass
canv_pruned.SaveAs(filename+'/ThreshPrunedSummary.png')


canv_proj = r.TCanvas('canv_proj_pruned', 'canv_proj_pruned', 500*8, 500*3)
canv_proj.Divide(8,3)
r.gStyle.SetOptStat(0)
print 'Saving File'
for i in range(0,24):
    r.gStyle.SetOptStat(0)
    canv_proj.cd(i+1)
    r.gPad.SetLogy()
    vSum[i].ProjectionY().Draw()
    vSum[i].ProjectionY().Write()
    pass
canv_proj.SaveAs(filename+'/VFATPrunedSummary.png')
#outF.Close()

#Now determine what VT1 to use for configuration.  The first threshold bin with no entries for now.
#Make a text file readable by TTree::ReadFile
vt1 = {}
for i in range(0,24):
    if (vfat_mask >> i) & 0x1: continue
    for j in range(VT1_MAX+1,0,-1):
        if (vSum[i].ProjectionY().GetBinContent(j+1)) > 10.0:
            print 'vt1 for VFAT %i found'%i
            vt1[i]=(j+1)
            break
        pass
    pass
outF.Close()
txt = open(filename+"/vfatConfig.txt", 'w')

print "trimRange:"
print trimRange
print "vt1:"
print vt1

txt.write("vfatN/I:vt1/I:trimRange/I\n")
for i in range(0,24):
    if (vfat_mask >> i) & 0x1: continue
    txt.write('%i\t%i\t%i\n'%(i, vt1[i],trimRange[i]))
    pass
txt.close()

#After Summary Thresh is made, subtract them before calling ProjectionY
#Output the first VThresh bi  with 0 ProjectionY in a text file
