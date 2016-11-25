#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 09:29:24 2016

@author: Hugo, Geng, Brian
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy
from scipy import special
from scipy.optimize import curve_fit
from ROOT import gROOT, gDirectory, TNamed, TLegend, TCanvas, TGraph, TH1F, TH2F, TFile, TDirectory #Classes
from ROOT import kGreen, kYellow, kBlue, kRed #Colors
import numpy as np
import os
import glob
choose = glob.glob("*Data_GLIB_IP_192*")
print
themean=[]
thesigma=[]
Tmean=[]
Tsigma=[]
print 
print "---------------- List Of the Files --------------"
for path, subdirs, files in os.walk(r'./'):
    meanALL = [] #to plot VCal means for all channels on all chips
    VCALmean14 = [] #to plot VCal means for one channel (14) for all chips
    covALL = [] #to plot VCal covs for all channels on all chips
    VCALcov14 = [] #to plot VCal covs for one channel (14) for all chips
    thresholdALL = [] #to plot thresholds for all chips

    file_Output_A = TFile("ScurveOutput.root","RECREATE","",1)
    dir_A_ChipID            = file_Output_A.mkdir("ChipID")
    dir_A_Thresholds        = file_Output_A.mkdir("Thresholds")
    dir_A_TrimDACValues     = file_Output_A.mkdir("TrimDACValues")
    dir_A_SCurveMeanByChan  = file_Output_A.mkdir("SCurveMeanByChannel")
    dir_A_SCurveSigma       = file_Output_A.mkdir("SCurvesSigma")
    dir_A_SCurveByChan      = file_Output_A.mkdir("SCurveByChannel")
    dir_A_SCurveExample     = file_Output_A.mkdir("SCurveExample")
    dir_A_SCurveSeparation  = file_Output_A.mkdir("SCurveSeparation")
    for fname in files:
        cities = fname.split("_")
        for city in cities:
            if city == 'Data':
                #print fname
                TestName = str(cities[0]+"_"+cities[1]+"_"+cities[2]+"_"+cities[3])
                slot     = int(cities[10])-160
                pos      = cities[12]
                port     = cities[14]
                #Declare the file
                #TFile file_Output_A = Open("%s_ScurveOutput.root"%(TestName), "w")
                #if file_Output_A is 0: 
                #file_Output_A = TFile("%s_ScurveOutput.root"%(TestName),"RECREATE","",1)
                file_Output_S = TFile("%s_VFAT%s_ID_%s_ScurveOutput.root"%(TestName,pos,port),"RECREATE","",1)
                #dir_A_ChipID            = file_Output_A.mkdir("ChipID")
                #dir_A_Thresholds        = file_Output_A.mkdir("Thresholds")
                #dir_A_TrimDACValues     = file_Output_A.mkdir("TrimDACValues")
                #dir_A_SCurveMeanByChan  = file_Output_A.mkdir("SCurveMeanByChannel")
                #dir_A_SCurveSigma       = file_Output_A.mkdir("SCurvesSigma")
                #dir_A_SCurveByChan      = file_Output_A.mkdir("SCurveByChannel")
                #dir_A_SCurveSeparation  = file_Output_A.mkdir("SCurveSeparation")
                dir_S_ChipID            = file_Output_S.mkdir("ChipID")
                dir_S_Thresholds        = file_Output_S.mkdir("Thresholds")
                dir_S_TrimDACValues     = file_Output_S.mkdir("TrimDACValues")
                dir_S_SCurveMeanByChan  = file_Output_S.mkdir("SCurveMeanByChannel")
                dir_S_SCurveSigma       = file_Output_S.mkdir("SCurvesSigma")
                dir_S_SCurveByChan      = file_Output_S.mkdir("SCurveByChannel")
                dir_S_SCurveExample     = file_Output_S.mkdir("SCurveExample")
                dir_S_SCurveSeparation  = file_Output_S.mkdir("SCurveSeparation")
                chipID = TNamed("VFAT%s"%(pos), str(port))
                dir_A_ChipID.cd()
                chipID.Write()
                dir_S_ChipID.cd()
                chipID.Write()
                Canvas = TCanvas()
#print choose
#TestName = raw_input("> Name of the Test? [Name Before '_Data_...'] : ")
#slot = raw_input("> GLIB slot used for the test? [1-12]: ")
#pos  = raw_input("> Position? [0-23]: ")
#port = raw_input("> ID of the VFAT2? : ")

#Number of the channel for which the SCURVE and its fit are printed.
                SCUVRE = 15
# build a rectangle in axes coords


                threshold1x = []
                threshold1y = []
                scurvex = []
                scurvey = []
                threshold2x = []
                threshold2y = []
                mean = []
                cov = []
                ma = np.zeros(shape=(128,255))
                count=0
                meanthreshold=0
                meanthreshold1=0
                sigmathreshold=0
                sigmathreshold1=0
                SCName = "S_CURVE_" + str(SCUVRE+1)

#Read the file Data_GLIB_IP_192_168_0_161_VFAT2_X_ID_Y with the 2 threshold- 
#Scans and the final Scurve by channel VFAT
                print str(TestName)+"_Data_GLIB_IP_192_168_0_"+str(160+int(slot))+"_VFAT2_"+str(pos)+"_ID_"+str(port)
                filename = glob.glob(str(TestName)+"_Data_GLIB_IP_192_168_0_"+str(160+int(slot))+"_VFAT2_"+str(pos)+"_ID_"+str(port)+"*")
                if filename == []:
                    print "No VFAT2 with ID " +str(port)+" at the position " + str(pos) + " with name " +str(TestName)
                for k in range(0,len(filename)):
                    filename = glob.glob(str(TestName)+"_Data_GLIB_IP_192_168_0_"+str(160+int(slot))+"_VFAT2_"+str(pos)+"_ID_"+str(port)+"*")[k]
                    threshold1x = []
                    threshold1y = []
                    scurvex = []
                    scurvey = []
                    threshold2x = []
                    threshold2y = []
                    mean = []
                    cov = []
                    ma = np.zeros(shape=(128,255))
                    count=0
                    f=open(filename)

                    line = (f.readline()).rstrip('\n')
                    thresholdValue = (float(line.strip('Threshold set to: ')))
                    thresholdALL.append(thresholdValue)
                    print line
                    if line == "0": #If no threshold have been set, VFAT2 is all 0 or all 1
                        print "Broken VFAT"
                        while (line != ""):
                            threshold1x.append(float(line))
                            threshold1y.append(float((f.readline()).rstrip('\n')))
                            line = (f.readline()).rstrip('\n') 
                        plt.xlim(0,255)
                        plt.plot(threshold1x, threshold1y,'bo')
                        plt.show()
                    else :
                        line = (f.readline()).rstrip('\n')
                        while ("S_CURVE" not in line): #Read the first TH Scan
                            if line == "":
                                break
                            threshold1x.append(float(line))
                            threshold1y.append(float((f.readline()).rstrip('\n')))
                            line = (f.readline()).rstrip('\n')
                        def fitFunc(t, mu, sigma, y0, p0): #Def of the erf function for the fit
                            return y0+(p0/2)*scipy.special.erf((np.sqrt(2)*(t-mu))/sigma)
                        if line != "":
                            line = (f.readline()).rstrip('\n')
                            while True:  #Read all the SCurve   
                                while ("S_CURVE" not in line or "" not in line):
                                    if "second_threshold" in line:
                                        break
                                    scurvex.append(float(line))
                                    line = (f.readline()).rstrip('\n')
                                    scurvey.append(float(line))
                                    line = (f.readline()).rstrip('\n')  
                                ma[count]=scurvey
                                count = count+1
                                while 0 in scurvey:
                                    scurvey.pop(0)
                                    scurvex.pop(0)
                                while 1 in scurvey:
                                    scurvey.pop(len(scurvey)-1)
                                    scurvex.pop(len(scurvex)-1)
                                scurvex2 = []
                                for i in scurvex:
                                    scurvex2.append(i-min(scurvex))
                                if SCName in line:
                                    scurvex3 = []
                                    fit=[]
                                    t = np.linspace(min(scurvex2), max(scurvex2), 250)
                                    fitParams, fitCovariances = curve_fit(fitFunc, scurvex2, scurvey)
                                    for i in t:
                                        fit.append(fitFunc(i, fitParams[0], fitParams[1],fitParams[2],fitParams[3]))
                                    #print "---------- Scurve and the erf fit of channel " + str(SCUVRE) + " in the transition zone ----------"    
                                    gScurveExample = TGraph(len(scurvex))
                                    for iPos in range(0,len(scurvex)):
                                        gScurveExample.SetPoint(iPos,scurvex[iPos],scurvey[iPos])
                                    gScurveExample.SetName( "VFAT%s_ID_%s_Scurve15"%(pos,port) )
                                    gScurveExample.SetMarkerColor(kBlue)
                                    gScurveExample.SetMarkerStyle(20)
                                    gScurveExample.SetTitle("S-curve on Channel %s of Chip %s at Position %s"%(SCUVRE, port,pos))
                                    gScurveExample.GetXaxis().SetTitle("Calibration pulse")
                                    gScurveExample.GetYaxis().SetTitle("Efficiency")
                                    gScurveExample.GetXaxis().SetRangeUser(min(scurvex),max(scurvex))
                                    gScurveExample.GetYaxis().SetRangeUser(0,1)
                                    gScurveExample.Draw('AP')
                                    gScurveExample_f = TGraph(len(t))
                                    for iPos in range(0,len(t)):
                                        gScurveExample_f.SetPoint(iPos,t[iPos]+min(scurvex),fit[iPos])
                                    gScurveExample_f.SetLineColor(kRed)
                                    gScurveExample_f.Draw('L SAME')
                                    dir_A_SCurveExample.cd()
                                    gScurveExample.Write()
                                    Canvas.Write("VFAT%s_ID_%s_Scurve15Fit"%(pos,port))
                                    dir_S_SCurveExample.cd()
                                    gScurveExample.Write()
                                    Canvas.Write("VFAT%s_ID_%s_Scurve15Fit"%(pos,port))
                                    scurvex3 = []
                                    VCALmean14.append(fitParams[0]+min(scurvex))
                                    VCALcov14.append(fitParams[1])
                                if scurvey==[]: #If the SCURVE of a channel was only 1 or 0
                                    print "line " + str(line) + "-1 is broken"
                                    mean.append(0) #If the channel is broken, the mean and covariance of the are set to 0
                                    meanALL.append(0)
                                    cov.append(0)
                                    covALL.append(0)
                                    scurvex = []
                                    scurvey = []
                                    scurvex2 = []
                                    line = (f.readline()).rstrip('\n')
                                    continue
                                try: # Fit the SCurve with the erf function
                                    fitParams, fitCovariances = curve_fit(fitFunc, scurvex2, scurvey)
                                    mean.append(fitParams[0]+min(scurvex))
                                    meanALL.append(fitParams[0]+min(scurvex))
                                    cov.append(fitParams[1])
                                    covALL.append(fitParams[1])
                                    themean.append(fitParams[0]+min(scurvex))
                                    thesigma.append(fitParams[1])
                                    meanthreshold1 = meanthreshold + fitParams[0]+min(scurvex)
                                    meanthreshold = meanthreshold1
                                    sigmathreshold1 = sigmathreshold + fitParams[1]
                                    sigmathreshold = sigmathreshold1
                                except: #If the SCURVE of a channel can not be fit
                                    print "line" + str(line) + "-1 is broken"
                                    mean.append(0) #If the channel is broken, the mean and covariance of the are set to 0
                                    meanALL.append(0)
                                    cov.append(0)
                                    covALL.append(0)
                                if "S_CURVE_128" in line:
                                    break
                                if "second_threshold" in line:
                                    Tmean.append(meanthreshold/128.)
                                    Tsigma.append(sigmathreshold/128.)
                                    break
                                scurvex = []
                                scurvey = []
                                scurvex2 = []
                                line = (f.readline()).rstrip('\n')
                                
                            line = (f.readline()).rstrip('\n')   
                            while (line != ""):
                                threshold2x.append(float(line))
                                threshold2y.append(float((f.readline()).rstrip('\n')))
                                line = (f.readline()).rstrip('\n')
                            f.close()
# Plot the 2 TH Scans
                        #print("---------- Threshold Scans ----------")    
                        #Make & store threshold TGraph before Trim
                        gThresh_PreTrim = TGraph(len(threshold1x))
                        #gThresh_PreTrim = TGraph(len(threshold1x), threshold1x, threshold1y)
                        for iPos in range(0,len(threshold1x)):
                            gThresh_PreTrim.SetPoint(iPos,threshold1x[iPos],threshold1y[iPos])
                        gThresh_PreTrim.SetName( "VFAT%s_ID_%s_thresholdsBefore"%(pos,port) )
                        gThresh_PreTrim.SetLineColor(kBlue)
                        gThresh_PreTrim.SetMarkerColor(kBlue)
                        gThresh_PreTrim.SetMarkerStyle(20)
                        gThresh_PreTrim.SetTitle("Initial Threshold Scan of Chip %s at Position %s"%(port,pos))
                        gThresh_PreTrim.GetXaxis().SetTitle("Threshold")
                        gThresh_PreTrim.GetYaxis().SetTitle("Noise")
                        gThresh_PreTrim.GetXaxis().SetRangeUser(min(threshold1x),max(threshold1x))
                        gThresh_PreTrim.GetYaxis().SetRangeUser(0,100)
                        dir_A_Thresholds.cd()
                        gThresh_PreTrim.Write()
                        dir_S_Thresholds.cd()
                        gThresh_PreTrim.Write()
                        
                        #Make & store threshold TGraph after Trim
                        if threshold2x == []:
                            print "Only the TH worked for", str(filename)
                            continue
                        gThresh_PostTrim = TGraph(len(threshold2x))
                        #gThresh_PostTrim = TGraph(len(threshold2x), threshold2x, threshold2y)
                        for iPos in range(0,len(threshold2x)):
                            gThresh_PostTrim.SetPoint(iPos,threshold2x[iPos],threshold2y[iPos])
                        gThresh_PostTrim.SetName( "VFAT%s_ID_%s_thresholdsAfter"%(pos,port) )
                        gThresh_PostTrim.SetLineColor(kRed)
                        gThresh_PostTrim.SetMarkerColor(kRed)
                        gThresh_PostTrim.SetMarkerStyle(21)
                        gThresh_PostTrim.SetTitle("Threshold Scan After Setting TrimDAC Values of Chip %s at Position %s"%(port,pos))
                        gThresh_PostTrim.GetXaxis().SetTitle("Threshold")
                        gThresh_PostTrim.GetYaxis().SetTitle("Noise")
                        gThresh_PostTrim.GetXaxis().SetRangeUser(min(threshold2x),max(threshold2x))
                        gThresh_PostTrim.GetYaxis().SetRangeUser(0,max(threshold2y))
                        dir_A_Thresholds.cd()
                        gThresh_PostTrim.Write()
                        dir_S_Thresholds.cd()
                        gThresh_PostTrim.Write()
                        
                        gThresh_PreTrim.SetTitle("Threshold Scan of Chip %s at Position %s"%(port,pos))
                        gThresh_PreTrim.GetYaxis().SetRangeUser(0,max(threshold2y))
                        gThresh_PreTrim.Draw('AP')
                        gThresh_PostTrim.Draw('P SAME')
                        legend = TLegend(0.60, 0.70, 0.89, 0.89)
                        legend.AddEntry(gThresh_PreTrim, "Initial Threshold Scan","P")
                        legend.AddEntry(gThresh_PostTrim, "Second Threshold Scan","P")
                        legend.Draw('SAME')
                        dir_A_Thresholds.cd()
                        Canvas.Write("VFAT%s_ID_%s_thresholds"%(pos,port))
                        dir_S_Thresholds.cd()
                        Canvas.Write("VFAT%s_ID_%s_thresholds"%(pos,port))
                        legend.Clear()
                        Canvas.Clear()

                        #print("---------- Mean of the Erf Function by channel ----------")
                        #Make & store Mean of Erf by Channel TGraph
                        gErfMeanByChan = TGraph(len(mean))
                        for iPos in range(0,len(mean)):
                            gErfMeanByChan.SetPoint(iPos,iPos,mean[iPos])
                        gErfMeanByChan.SetName( "VFAT%s_ID_%s_meanerfbychan"%(pos,port) )
                        gErfMeanByChan.SetLineColor(kBlue)
                        gErfMeanByChan.SetMarkerColor(kBlue)
                        gErfMeanByChan.SetMarkerStyle(20)
                        gErfMeanByChan.SetTitle("S-curve Mean Values of Chip %s at Position %s"%(port,pos))
                        gErfMeanByChan.GetXaxis().SetTitle("128 Strip Channels")
                        gErfMeanByChan.GetYaxis().SetTitle("Calibration pulse 50% Turn-on Point [per Channel]")
                        gErfMeanByChan.GetXaxis().SetRangeUser(0,127)
                        gErfMeanByChan.GetYaxis().SetRangeUser(0,255)
                        dir_A_SCurveMeanByChan.cd()
                        gErfMeanByChan.Write()
                        dir_S_SCurveMeanByChan.cd()
                        gErfMeanByChan.Write()
                        
                        #print("---------- cov of the Erf Function by channel ----------")
                        #Make & store Cov of Erf by Channel TGraph
                        gErfCovByChan = TGraph(len(cov))
                        for iPos in range(0,len(cov)):
                            gErfCovByChan.SetPoint(iPos,iPos,cov[iPos])
                        gErfCovByChan.SetName( "VFAT%s_ID_%s_coverfbychan"%(pos,port) )
                        gErfCovByChan.SetLineColor(kRed)
                        gErfCovByChan.SetMarkerColor(kRed)
                        gErfCovByChan.SetMarkerStyle(20)
                        gErfCovByChan.SetTitle("S-curve Sigma of Chip %s at Position %s"%(port,pos))
                        gErfCovByChan.GetXaxis().SetTitle("128 Strip Channels")
                        gErfCovByChan.GetYaxis().SetTitle("S-curve Sigma of the Erf Function by Channel [per Channel]")
                        gErfCovByChan.GetXaxis().SetRangeUser(0,127)
                        dir_A_SCurveSigma.cd()
                        gErfCovByChan.Write()
                        dir_S_SCurveSigma.cd()
                        gErfCovByChan.Write()
                        
                        #print("---------- Histogram of the covariance of the Erf Function ----------")
                        #Make & store Cov of Erf by Channel Histogram
                        hCovHistogram = TH1F("VFAT%s_ID_%s_coverfHist"%(pos,port), "", 500,0,100 )
                        for iPos in range(0,len(cov)):
                            hCovHistogram.Fill(cov[iPos])
                        hCovHistogram.SetFillColor(kGreen)
                        hCovHistogram.SetTitle("S-curve Sigma Histogram  of Chip %s at Position %s; S-curve Sigma; "%(port,pos))
                        hCovHistogram.GetXaxis().SetRangeUser(min(cov)*0.8,max(cov)*1.2)
                        hCovHistogram.Draw('H')
                        dir_A_SCurveSigma.cd()
                        hCovHistogram.Write()
                        dir_S_SCurveSigma.cd()
                        hCovHistogram.Write()
                        Canvas.Clear()
                        
                        #Read and plot the SCurve before the scan                       
                        fi = glob.glob(str(TestName)+"_SCurve_by_channel_VFAT2_"+str(pos)+"_ID_"+str(port)+"*")[k]
                        g=open(fi)
                                
                        maSC = np.zeros(shape=(128,255))
                        count = 0
                        line = (g.readline()).rstrip('\n')
                        line = (g.readline()).rstrip('\n')
                        SCx = []
                        SCy = []
                        while True:     
                            while ("SCurve" not in line):
                                if not line: break
                                SCx.append(float(line))
                                line = (g.readline()).rstrip('\n')
                                SCy.append(float(line))
                                line = (g.readline()).rstrip('\n')
                            if not line: break
                            maSC[count]=SCy
                            count = count+1 
                            SCx = []
                            SCy = []
                            line = (g.readline()).rstrip('\n')
                        g.close()
                        #print("---------- S-Curve by channel Before the Script ----------")    
                        #Make & store SCurves by Chan No. Before Trimming
                        h2DSCurveByChanPreTrim = TH2F( "VFAT%s_ID_%s_scurvebefore"%(pos,port), "", 255,0,255, 127, 0, 127)
                        for index, valSCurve in np.ndenumerate(maSC):
                            h2DSCurveByChanPreTrim.SetBinContent(index[1]+1,index[0]+1, valSCurve )
                        h2DSCurveByChanPreTrim.SetTitle("Initial S-curve of Chip %s at Position %s"%(port,pos))
                        h2DSCurveByChanPreTrim.GetXaxis().SetTitle("S-curve: Calibration Pulse")
                        h2DSCurveByChanPreTrim.GetYaxis().SetTitle("128 Strip Channels")
                        h2DSCurveByChanPreTrim.SetStats(0)
                        h2DSCurveByChanPreTrim.Draw('colz')
                        dir_A_SCurveByChan.cd()
                        h2DSCurveByChanPreTrim.Write()
                        Canvas.Write("VFAT%s_ID_%s_ScurveBF"%(pos,port))
                        dir_S_SCurveByChan.cd()
                        h2DSCurveByChanPreTrim.Write()
                        Canvas.Write("VFAT%s_ID_%s_ScurveBF"%(pos,port))
                        Canvas.Clear()
                        
                        # Plot the S_Curve after fitting
                        #print("---------- S-Curve by channel after the Script ----------")
                        #Make & store SCurves by Chan No. After Trimming
                        h2DSCurveByChanPostTrim = TH2F( "VFAT%s_ID_%s_scurveafter"%(pos,port), "", 255,0,255, 127, 0, 127)
                        for index, valSCurve in np.ndenumerate(ma):
                            h2DSCurveByChanPostTrim.SetBinContent(index[1]+1,index[0]+1, valSCurve )
                        h2DSCurveByChanPostTrim.SetTitle("After setting TrimDAC Values S-curve of Chip %s at Position %s"%(port,pos))
                        h2DSCurveByChanPostTrim.GetXaxis().SetTitle("S-curve: Calibration Pulse")
                        h2DSCurveByChanPostTrim.GetYaxis().SetTitle("128 Strip Channels")
                        h2DSCurveByChanPostTrim.SetStats(0)
                        h2DSCurveByChanPostTrim.Draw('colz')
                        dir_A_SCurveByChan.cd()
                        h2DSCurveByChanPostTrim.Write()
                        Canvas.Write("VFAT%s_ID_%s_ScurveAF"%(pos,port))
                        dir_S_SCurveByChan.cd()
                        h2DSCurveByChanPostTrim.Write()
                        Canvas.Write("VFAT%s_ID_%s_ScurveAF"%(pos,port))
                        Canvas.Clear()
                        
                        
                        #Read and plot the TrimDAC values                       
                        fi = glob.glob(str(TestName)+"_TRIM_DAC_value_VFAT_"+str(pos)+"_ID_"+str(port)+"*")[k]
                        g=open(fi)
                        trim = []
                        while True:     
                            line = (g.readline()).rstrip('\n')
                            if not line: break
                            trim.append(int(line))
                        g.close()
                        gTrimDAC = TGraph(len(trim))
                        for iPos in range(0,len(trim)):
                            gTrimDAC.SetPoint(iPos,iPos,trim[iPos])
                        gTrimDAC.SetName( "VFAT%s_ID_%s_TrimDAC"%(pos,port) )
                        gTrimDAC.SetMarkerColor(kBlue)
                        gTrimDAC.SetLineColor(kBlue)
                        gTrimDAC.SetMarkerStyle(20)
                        gTrimDAC.SetTitle("TrimDAC Values of Chip %s at Position %s"%(port,pos))
                        gTrimDAC.GetXaxis().SetTitle("128 Strip Channels")
                        gTrimDAC.GetYaxis().SetTitle("TrimDAC Value")
                        gTrimDAC.GetXaxis().SetRangeUser(0,127)
                        gTrimDAC.GetYaxis().SetRangeUser(0,max(trim)*1.5)
                        dir_A_TrimDACValues.cd()
                        gTrimDAC.Write()
                        dir_S_TrimDACValues.cd()
                        gTrimDAC.Write()
                    
                    
                        #print("---------- Histogram of the '0.5 point' for a TrimDAC of 0/31 and after the Script ----------")   
                        vcal0 = []
                        vcal31 = []
                        vcalfinal = []
                        filename = glob.glob(str(TestName)+"_VCal_VFAT2_"+str(pos)+"_ID_" + str(port))[k]
                        f=open(filename,'r')
                        line = (f.readline()).rstrip('\n')
                        vcal= line.split()
                        for ele in vcal:
                            if ele.startswith('['):
                                ele = ele[1:]
                            ele = ele.rstrip(']') 
                            ele = ele.rstrip('L,') 
                            vcal0.append(int(ele))
                        line = (f.readline()).rstrip('\n')
                        vcal= line.split()
                        for ele in vcal:
                            if ele.startswith('['):
                                ele = ele[1:]
                            ele = ele.rstrip(']') 
                            ele = ele.rstrip('L,') 
                            vcal31.append(int(ele))
                        
                        line = (f.readline())
                        vcal= line.split()
                        for ele in vcal:
                            if ele.startswith('['):
                                ele = ele[1:]
                            ele = ele.rstrip(']') 
                            ele = ele.rstrip('L,') 
                            vcalfinal.append(int(ele))
                        
                        vcal0Hist = TH1F("VFAT%s_ID_%s_0.5PointHist0"%(pos,port), "", 255,0,255 )
                        for iPos in range(0,len(vcal0)):
                            vcal0Hist.Fill(vcal0[iPos])
                        vcal0Hist.SetStats(0)
                        vcal0Hist.SetFillColor(kGreen)
                        vcal0Hist.SetTitle("Histogram of the '0.5 point' for a TrimDAC of 0/31 and True Value; ; ")
                        vcal0Hist.GetXaxis().SetRangeUser(min(vcal0)*0.5,max(vcal0)*1.5)
                        vcal0Hist.Draw('H')
                        vcal31Hist = TH1F("VFAT%s_ID_%s_0.5PointHist31"%(pos,port), "", 255,0,255 )
                        for iPos in range(0,len(vcal31)):
                            vcal31Hist.Fill(vcal31[iPos])
                        vcal31Hist.SetStats(0)
                        vcal31Hist.SetFillColor(kBlue)
                        vcal31Hist.Draw('H SAME')
                        vcalHist = TH1F("VFAT%s_ID_%s_0.5PointHist"%(pos,port), "", 255,0,255 )
                        for iPos in range(0,len(vcalfinal)):
                            vcalHist.Fill(vcalfinal[iPos])
                        vcalHist.SetStats(0)
                        vcalHist.SetFillColor(kRed)
                        vcalHist.Draw('H SAME')
                        legend.AddEntry(vcal0Hist, " TrimDAC 0","F")
                        legend.AddEntry(vcal31Hist, " TrimDAC 31","F")
                        legend.AddEntry(vcalHist, " TrimDAC Values","F")
                        legend.Draw('SAME')
                        dir_A_SCurveSeparation.cd()
                        Canvas.Write("VFAT%s_ID_%s_0.5PointHist"%(pos,port))
                        dir_S_SCurveSeparation.cd()
                        Canvas.Write("VFAT%s_ID_%s_0.5PointHist"%(pos,port))
                        Canvas.Close()
#Close Output ROOT File
                file_Output_S.Close()
                #file_Output_A.Close()
    file_Output_A.Close()
