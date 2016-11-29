#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 19:02:34 2016
@author: Geng

"""

from ROOT import gROOT, gDirectory, TMultiGraph, TNamed, TLegend, TCanvas, TGraph, TH1F, TH2F, TFile, TDirectory #Classes
from ROOT import kGreen, kYellow, kBlue, kRed #Colors
import ROOT as rt
rt.gROOT.SetBatch(True)
import numpy as np
import os
import glob

pos  = []
port = []
VFAT = []
TrimFiles = []
TrimValue = []
MaskValue = 0
sigmaY = []
file_Read_A  = TFile('ScurveOutput.root', 'r') # a file

## Read the chipID and Positions
file_Read_A.cd('ChipID')
for iPos in range(24):
    VFAT2s = gDirectory.Get('VFAT%s'%iPos)
    if bool(VFAT2s) is False:
        pos.append(str('VFAT%s'%iPos))
        port.append(str(False))
        continue
    pos.append(str(VFAT2s.GetName()))
    port.append(str(VFAT2s.GetTitle()))

## Plot 3 S-curves for different iEta region
gDirectory.cd('../SCurveExample')
for iPos in range(24):
    VFAT2s = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[iPos], port[iPos]))
    if bool(VFAT2s) is False:
        VFAT.append(VFAT2s)
        port[iPos]='False'
        continue
    VFAT.append(VFAT2s)
for i in range(0,8):
    ieta = 8 - i
    Canvas = TCanvas("Canvas", "Canvas")
    mg = TMultiGraph("mg","S-curve on Channel 15 of iEta %s; Calibration pulse; "%(ieta))
    legend = TLegend(0.72, 0.11, 0.89, 0.23)
    ## iPhi = 3
    VFAT[i]    = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[i], port[i]))
    if bool(VFAT[i]) is False:
        port[iPos]='False'
        continue
    else:
        VFAT[i].SetLineColor(kRed)
        VFAT[i].SetMarkerColor(kRed)
        VFAT[i].SetMarkerStyle(20)
        mg.Add(VFAT[i],"lp")
        legend.AddEntry(VFAT[i], "%s  : %s"%(pos[i], port[i+0]),"lP")
    ## iPhi = 2
    VFAT[i+8]  = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[i+8], port[i+8]))
    if bool(VFAT[i+8]) is False:
        port[iPos]='False'
        continue
    else:
        VFAT[i+8].SetLineColor(kBlue)
        VFAT[i+8].SetMarkerColor(kBlue)
        VFAT[i+8].SetMarkerStyle(22)
        mg.Add(VFAT[i+8],"lp")
        legend.AddEntry(VFAT[i+8], "%s  : %s"%(pos[i+8], port[i+8]),"lP")
    ## iPhi = 1
    VFAT[i+16] = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[i+16], port[i+16]))
    if bool(VFAT[i+16]) is False:
        port[iPos]='False'
        continue
    else:
        VFAT[i+16].SetLineColor(kGreen)
        VFAT[i+16].SetMarkerColor(kGreen)
        VFAT[i+16].SetMarkerStyle(24)
        mg.Add(VFAT[i+16],"lp")
        legend.AddEntry(VFAT[i+16], "%s: %s"%(pos[i+16], port[i+16]),"lP")
    mg.Draw("SAME")
    legend.Draw('SAME')
    Canvas.Print('iEta_%s_ScurveAF.pdf'%(ieta))

## Read TrimDAC Values
gDirectory.cd('../TrimDACValues')
for iPos in range(24):
    if port[iPos] is 'False':
        continue
    VFAT2s_T = gDirectory.Get('%s_ID_%s_TrimDAC'%(pos[iPos], port[iPos]))
    if bool(VFAT2s_T) is False:
        port[iPos]='False'
        continue
    TrimFiles.append(VFAT2s_T)
## Read S-curve sigma Values
gDirectory.cd('../SCurvesSigma')
gg=open("All_Bad_Channels_to_Mask",'w')
for iPos in range(24):
    if port[iPos] is 'False':
        continue
    VFAT2s_H = gDirectory.Get('%s_ID_%s_coverfHist'%(pos[iPos], port[iPos]))
    VFAT2s_S = gDirectory.Get('%s_ID_%s_coverfbychan'%(pos[iPos], port[iPos]))
    CovMean  = VFAT2s_H.GetMean()
    CovSigma = VFAT2s_H.GetStdDev()
    sigmaY   = VFAT2s_S.GetY()
    TrimValue = TrimFiles[iPos].GetY()
    g=open("Mask_TRIM_DAC_value_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    gg.write("chipID_"+port[iPos]+'\n')
    for iP in range(0,128):
        ## Method to define the bad channels:   
        ### (sigma < CovMean-2.5*CovSigma) 
        ### (sigma > CovMean+2.5*CovSigma) or ( sigma == 0) 
        if ( sigmaY[iP] < (CovMean-2.5*CovSigma) ) or ( sigmaY[iP] > (CovMean+2.5*CovSigma) ) or ( sigmaY[iP]==0  ): 
            gg.write(str(iP)+'\n')
            #print str(iP)+"\t\t\t"+str(TrimValue[iP])+"\t\t\t"+"1" 
            MaskValue = 1 
        else: 
            #print str(iP)+"\t\t\t"+str(TrimValue[iP])+"\t\t\t"+"0" 
            MaskValue = 0 
        g.write('%d\t\t\t%d\t\t\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue)))
        #g.write(str(iP)+'\t\t\t'+str(int(TrimValue[iP]))+'\t\t\t'+str(MaskValue)+'\n')


file_Read_A.Close()
