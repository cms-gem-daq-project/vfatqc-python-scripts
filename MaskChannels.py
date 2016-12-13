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
TrimFiles = []
MeanValue = []
TrimValue = []
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

## Read TrimDAC Values
gDirectory.cd('../TrimDACValues')
for iPos in range(24):
    VFAT2s_T = gDirectory.Get('%s_ID_%s_TrimDAC'%(pos[iPos], port[iPos]))
    if bool(VFAT2s_T) is False:
        TrimFiles.append(VFAT2s_T)
        port[iPos]='False'
        continue
    TrimFiles.append(VFAT2s_T)
## Read S-curve mean values
gDirectory.cd('../SCurveMeanByChannel')
gg_M=open("All_Bad_Channels_to_Mask_by_MEAN",'w')
for iPos in range(24):
    if port[iPos] is 'False':
        continue
    Canvas = TCanvas("Canvas", "Canvas")
    frame = TH1F("frame","S-curve Mean Values of Chip %s at Position %s; 128 Strip Channels; Calibration pulse 50 percent Turn-on Point [per Channel];"%(port[iPos],pos[iPos]),127,0.,127)
    frame.SetAxisRange(0,255,"Y")
    frame.SetStats(kFALSE)
    frame.Draw()
    mg = TMultiGraph("mg","Mean")
    legend = TLegend(0.72, 0.72, 0.89, 0.89)
    Line_p0 = TLine(0,2,127,2)
    Line_p0.SetLineColor(4)
    Line_p0.Draw("SAME")
    legend.AddEntry(Line_p0, "cut if mean=0","L")
    VFAT2s_H  = gDirectory.Get('%s_ID_%s_meanerfbychan'%(pos[iPos], port[iPos]))
    mg.Add(VFAT2s_H,"pl")
    mg.Draw("P")
    MeanValue = VFAT2s_H.GetY()
    M_Mean    = VFAT2s_H.GetMean(2)
    M_RMS     = VFAT2s_H.GetRMS(2)
    TrimValue = TrimFiles[iPos].GetY()
    g_25=open("Mask_TRIM_DAC_value_by_MEAN_cut0_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    g_15=open("Mask_TRIM_DAC_value_by_MEAN_cut1_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    g_10=open("Mask_TRIM_DAC_value_by_MEAN_cut2_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    gg_M.write("chipID_"+port[iPos]+'\n')
    #print pos[iPos]+" : \nMean   = "+str(M_Mean)+"  RMS   = "+str(M_RMS)
    MaskValue = []
    test_Y_25 = []
    for iP in range(0,128):
        ## Method to define the bad channels:   
        ### (Channel_Mean > Mean*1.25) or ( Mean == 0) 
        if ((MeanValue[iP] > M_Mean*1.25) or (MeanValue[iP] == 0)):   
            gg_M.write(str(iP)+'\n')
            MaskValue.append(1) 
        elif (MeanValue[iP] < M_Mean*0.75):   
            MaskValue.append(0) 
        else: 
            test_Y_25.append(MeanValue[iP])
            MaskValue.append(0) 
        g_25.write('%d\t%d\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue[iP])))
    test_M_25 = 0.
    test_S_25 = 0.
    test_C_25 = len(test_Y_25)
    for iP in range(0,test_C_25):
        test_S_25 = test_S_25 + test_Y_25[iP]*test_Y_25[iP]
        test_M_25 = test_M_25 + test_Y_25[iP]
    Mean_25   = test_M_25/test_C_25
    RMS_25    = TMath.Sqrt(test_S_25/test_C_25 - TMath.Power(Mean_25,2))
    #print "Mean_25= "+str(Mean_25)+"  RMS_25= "+str(RMS_25)

    test_Y_15 = []
    for iP in range(0,128):
        ## Method to define the bad channels:   
        ### (Channel_Mean > Rest_Mean*1.15)  
        if (MeanValue[iP]> Mean_25*1.15):   
            gg_M.write(str(iP)+'\n')
            MaskValue[iP] = 1 
        elif (MeanValue[iP] < Mean_25*0.85):   
            MaskValue[iP] = 0 
        else: 
            test_Y_15.append(MeanValue[iP])
            MaskValue[iP] = 0 
        g_15.write('%d\t%d\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue[iP])))
    test_M_15 = 0.
    test_S_15 = 0.
    test_C_15 = len(test_Y_15)
    for iP in range(0,test_C_15):
        test_S_15 = test_S_15 + test_Y_15[iP]*test_Y_15[iP]
        test_M_15 = test_M_15 + test_Y_15[iP]
    Mean_15   = test_M_15/test_C_15
    RMS_15    = TMath.Sqrt(test_S_15/test_C_15 - TMath.Power(Mean_15,2))
    #print "Mean_15= "+str(Mean_15)+"  RMS_15= "+str(RMS_15)

    test_Y_10 = []
    for iP in range(0,128):
        ## Method to define the bad channels:   
        ### (Channel_Mean > Rest_Mean*1.10)  
        if (MeanValue[iP] > Mean_15*1.10):   
            gg_M.write(str(iP)+'\n')
            MaskValue[iP] = 1 
        elif (MeanValue[iP] < Mean_15*0.90):   
            MaskValue[iP] = 0 
        else: 
            test_Y_10.append(MeanValue[iP])
            MaskValue[iP] = 0 
        g_10.write('%d\t%d\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue[iP])))
    test_M_10 = 0.
    test_S_10 = 0.
    test_C_10 = len(test_Y_10)
    for iP in range(0,test_C_10):
        test_S_10 = test_S_10 + test_Y_10[iP]*test_Y_10[iP]
        test_M_10 = test_M_10 + test_Y_10[iP]
    Mean_10   = test_M_10/test_C_10
    RMS_10    = TMath.Sqrt(test_S_10/test_C_10 - TMath.Power(Mean_10,2))
    #print "Mean_10= "+str(Mean_10)+"  RMS_10= "+str(RMS_10)

    Line_p25 = TLine(0,M_Mean*1.25,127,M_Mean*1.25)
    Line_p25.SetLineColor(2)
    Line_p25.Draw("SAME")
    Line_m25 = TLine(0,M_Mean*0.75,127,M_Mean*0.75)
    Line_m25.SetLineColor(2)
    Line_m25.SetLineStyle(2)
    Line_m25.Draw("SAME")
    legend.AddEntry(Line_p25, "25% cut0","L")
    Line_p15 = TLine(0,Mean_25*1.15,127,Mean_25*1.15)
    Line_p15.SetLineColor(6)
    Line_p15.Draw("SAME")
    Line_m15 = TLine(0,Mean_25*0.85,127,Mean_25*0.85)
    Line_m15.SetLineColor(6)
    Line_m15.SetLineStyle(2)
    Line_m15.Draw("SAME")
    legend.AddEntry(Line_p15, "15% cut1","L")
    Line_p10 = TLine(0,Mean_15*1.10,127,Mean_15*1.10)
    Line_p10.SetLineColor(3)
    Line_p10.Draw("SAME")
    Line_m10 = TLine(0,Mean_15*0.90,127,Mean_15*0.90)
    Line_m10.SetLineColor(3)
    Line_m10.SetLineStyle(2)
    Line_m10.Draw("SAME")
    legend.AddEntry(Line_p10, "10% cut2","L")

    legend.Draw('SAME')
    Canvas.Print('%s_Mean_cut_%s.pdf'%(pos[iPos],port[iPos]))
    frame.Delete()
    Canvas.Close()

## Read S-curve sigma Values
MaskValue_S = 0
gDirectory.cd('../SCurvesSigma')
gg_S=open("All_Bad_Channels_to_Mask_by_SIGMA",'w')
for iPos in range(24):
    if port[iPos] is 'False':
        continue
    VFAT2s_H = gDirectory.Get('%s_ID_%s_coverfHist'%(pos[iPos], port[iPos]))
    VFAT2s_S = gDirectory.Get('%s_ID_%s_coverfbychan'%(pos[iPos], port[iPos]))
    CovMean  = VFAT2s_H.GetMean()
    CovSigma = VFAT2s_H.GetStdDev()
    sigmaY   = VFAT2s_S.GetY()
    TrimValue = TrimFiles[iPos].GetY()
    g_S=open("Mask_TRIM_DAC_value_by_SIGMA_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    gg_S.write("chipID_"+port[iPos]+'\n')
    for iP in range(0,128):
        ## Method to define the bad channels:   
        ### (sigma > CovMean+2.5*CovSigma) or ( sigma == 0) 
        if ( sigmaY[iP] > (CovMean+2.5*CovSigma) ) or ( sigmaY[iP]==0  ): 
            gg_S.write(str(iP)+'\n')
            MaskValue_S = 1 
        else: 
            MaskValue_S = 0 
        g_S.write('%d\t%d\t%d\n'%(int(iP),int(TrimValue[iP]),int(MaskValue_S)))

file_Read_A.Close()

## Combine two methods
for iPos in range(24):
    if port[iPos] is 'False':
        continue
    w_25=open("Mask_TRIM_DAC_value_by_SIGMA_and_MEAN_cut0_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    w_15=open("Mask_TRIM_DAC_value_by_SIGMA_and_MEAN_cut1_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    w_10=open("Mask_TRIM_DAC_value_by_SIGMA_and_MEAN_cut2_%s_ID_%s"%(pos[iPos], port[iPos]),'w')
    g_S =open("Mask_TRIM_DAC_value_by_SIGMA_%s_ID_%s"%(pos[iPos], port[iPos]),'r')
    g_25=open("Mask_TRIM_DAC_value_by_MEAN_cut0_%s_ID_%s"%(pos[iPos], port[iPos]),'r')
    g_15=open("Mask_TRIM_DAC_value_by_MEAN_cut1_%s_ID_%s"%(pos[iPos], port[iPos]),'r')
    g_10=open("Mask_TRIM_DAC_value_by_MEAN_cut2_%s_ID_%s"%(pos[iPos], port[iPos]),'r')
    while True:
        line_S  = (g_S.readline()).rstrip('\n')
        if not line_S: break
        line_25 = (g_25.readline()).rstrip('\n')
        line_15 = (g_15.readline()).rstrip('\n')
        line_10 = (g_10.readline()).rstrip('\n')
        vals_S  = line_S.split("\t")
        vals_25 = line_25.split("\t")
        vals_15 = line_15.split("\t")
        vals_10 = line_10.split("\t")
        if (vals_S[2]==vals_25[2]): 
            MaskValue_25 = vals_S[2]
        else: 
            MaskValue_25 = 1
        w_25.write('%d\t%d\t%d\n'%(int(vals_S[0]),int(vals_S[1]),int(MaskValue_25)))
        if (vals_S[2]==vals_15[2]): 
            MaskValue_15 = vals_S[2]
        else: 
            MaskValue_15 = 1
        w_15.write('%d\t%d\t%d\n'%(int(vals_S[0]),int(vals_S[1]),int(MaskValue_15)))
        if (vals_S[2]==vals_10[2]): 
            MaskValue_10 = vals_S[2]
        else: 
            MaskValue_10 = 1
        w_10.write('%d\t%d\t%d\n'%(int(vals_S[0]),int(vals_S[1]),int(MaskValue_10)))
        pass



