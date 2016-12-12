#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 19:02:34 2016
@author: Geng

"""
from ROOT import *
gROOT.SetBatch(True)

pos  = []
port = []
VFAT = []
VFAT_S = []
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

## Plot S-curves of 3 chips for different iEta region
gDirectory.cd('../SCurveByChannel')
for iPos in range(24):
    VFAT2s = gDirectory.Get('%s_ID_%s_scurveafter'%(pos[iPos], port[iPos]))
    if bool(VFAT2s) is False:
        VFAT_S.append(VFAT2s)
        port[iPos]='False'
        continue
    VFAT_S.append(VFAT2s)
for i in range(0,8):
    ieta = 8 - i
    Canvas = TCanvas("Canvas", "Canvas")
    TH_SCurve = TH2F("TH_SCurve","After setting TrimDAC Values S-Curves of iEta %s; Calibration pulse; "%(ieta), 383, 0, 383, 255,0,255)
    ## iPhi = 1
    while bool(VFAT_S[i+16]) is True:
        VFAT_S[i+16] = gDirectory.Get('%s_ID_%s_scurveafter'%(pos[i+16], port[i+16]))
        for y in range(0,255): 
            for x in range(0,128):
                TH_SCurve.SetBinContent(x+1,y+1,VFAT_S[i+16].GetBinContent(x+1,y+1))
        break
    ## iPhi = 2
    while bool(VFAT_S[i+8]) is True:
        VFAT_S[i+8]  = gDirectory.Get('%s_ID_%s_scurveafter'%(pos[i+8], port[i+8]))
        for y in range(0,255): 
            for x in range(128,256):
                TH_SCurve.SetBinContent(x+1,y+1,VFAT_S[i+8].GetBinContent(x-127,y+1))
        break
    ## iPhi = 3
    while bool(VFAT_S[i]) is True:
        VFAT_S[i]    = gDirectory.Get('%s_ID_%s_scurveafter'%(pos[i], port[i]))
        for y in range(0,255): 
            for x in range(256,384):
                TH_SCurve.SetBinContent(x+1,y+1,VFAT_S[i].GetBinContent(x-255,y+1))
        break
    TH_SCurve.GetYaxis().SetTitle('S-curve: Calibration Pulse')
    TH_SCurve.GetXaxis().SetNdivisions(1,0,0)
    TH_SCurve.GetXaxis().SetTitle('')
    TH_SCurve.GetXaxis().SetLabelOffset(-0.01)
    TH_SCurve.GetXaxis().SetLabelSize(0.02)
    TH_SCurve.SetStats(0)
    TH_SCurve.Draw('colz')
    axis1 = TGaxis(0.,-3.,127,-3.,0,127,1,"+")
    axis1.SetTitle('%s_%s'%(pos[i+16], port[i+16]))
    axis1.CenterTitle()
    axis1.SetLineColor(4)
    axis1.SetTitleOffset(0.5)
    axis1.SetTextColor(4)
    axis1.SetLabelColor(4)
    axis1.Draw()
    axis2 = TGaxis(128,3.,255,3.,0,127,1,"-")
    axis2.SetTitle('%s_%s'%(pos[i+8], port[i+8]))
    axis2.CenterTitle()
    axis2.SetLineColor(3)
    axis2.SetTitleOffset(0.5)
    axis2.SetTextColor(3)
    axis2.SetLabelColor(3)
    axis2.Draw()
    axis3 = TGaxis(256,-3.,383,-3.,0,127,1,"+")
    axis3.SetTitle('%s_%s'%(pos[i], port[i]))
    axis3.CenterTitle()
    axis3.SetLineColor(2)
    axis3.SetTitleOffset(0.5)
    axis3.SetTextColor(2)
    axis3.SetLabelColor(2)
    axis3.Draw()
    Canvas.Print('iEta_%s_ScurveAF.pdf'%(ieta))
    TH_SCurve.Delete()
    Canvas.Close()

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
    while bool(VFAT[i]) is True:
        VFAT[i].SetLineColor(kRed)
        VFAT[i].SetMarkerColor(kRed)
        VFAT[i].SetMarkerStyle(20)
        mg.Add(VFAT[i],"p")
        legend.AddEntry(VFAT[i], "%s  : %s"%(pos[i], port[i+0]),"P")
        break
    ## iPhi = 2
    VFAT[i+8]  = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[i+8], port[i+8]))
    while bool(VFAT[i+8]) is True:
        VFAT[i+8].SetLineColor(kBlue)
        VFAT[i+8].SetMarkerColor(kBlue)
        VFAT[i+8].SetMarkerStyle(22)
        mg.Add(VFAT[i+8],"p")
        legend.AddEntry(VFAT[i+8], "%s  : %s"%(pos[i+8], port[i+8]),"P")
        break
    ## iPhi = 1
    VFAT[i+16] = gDirectory.Get('%s_ID_%s_Scurve15'%(pos[i+16], port[i+16]))
    while bool(VFAT[i+16]) is True:
        VFAT[i+16].SetLineColor(kGreen)
        VFAT[i+16].SetMarkerColor(kGreen)
        VFAT[i+16].SetMarkerStyle(24)
        mg.Add(VFAT[i+16],"p")
        legend.AddEntry(VFAT[i+16], "%s: %s"%(pos[i+16], port[i+16]),"P")
        break
    mg.Draw("SAME")
    legend.Draw('SAME')
    Canvas.Print('Example_ScurveAF_iEta_%s.pdf'%(ieta))
    Canvas.Close()

## Read TrimDAC Values
gDirectory.cd('../TrimDACValues')
for iPos in range(24):
    VFAT2s_T = gDirectory.Get('%s_ID_%s_TrimDAC'%(pos[iPos], port[iPos]))
    if bool(VFAT2s_T) is False:
        TrimFiles.append(VFAT2s_T)
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
            MaskValue = 1 
        else: 
            MaskValue = 0 
        g.write('%d\t%d\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue)))


file_Read_A.Close()
