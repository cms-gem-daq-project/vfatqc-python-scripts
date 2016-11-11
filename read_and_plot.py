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
from ROOT import gROOT, TGraph, TH1F, TH2F, TFile, TDirectory #Classes
from ROOT import kBlue, kRed #Colors
import numpy as np
import os
import glob
choose = glob.glob("*Data_GLIB_IP_192*")
print
themean=[]
thesigma=[]
Tmean=[]
Tsigma=[]

#Declare the file
file_Output = TFile("SCurveOutput.root","RECREATE","",1)

dir_SCurveCovariance = file_Output.mkdir("SCurveCovariance")
dir_SCurveExample = file_Output.mkdir("SCurveExample")
dir_SCurveMeanByChan = file_Output.mkdir("SCurveMeanByChan")
dir_SCurveSeparation = file_Output.mkdir("SCurveSeparation")
dir_SCurveSigmaByChan = file_Output.mkdir("SCurvesSigmaByChan")
dir_SCurveByChan = file_Output.mkdir("SCurveByChan")
dir_Threshold = file_Output.mkdir("Threshold")

print 
print "---------------- List Of the Files --------------"
for path, subdirs, files in os.walk(r'./'):
    meanALL = [] #to plot VCal means for all channels on all chips
    VCALmean14 = [] #to plot VCal means for one channel (14) for all chips
    covALL = [] #to plot VCal covs for all channels on all chips
    VCALcov14 = [] #to plot VCal covs for one channel (14) for all chips
    thresholdALL = [] #to plot thresholds for all chips

    for fname in files:
        cities = fname.split("_")
        for city in cities:
            if city == 'Data':
                #print fname
                TestName = str(cities[0]+"_"+cities[1]+"_"+cities[2]+"_"+cities[3])
                slot     = int(cities[10])-160
                pos      = cities[12]
                port     = cities[14]
#print choose
#TestName = raw_input("> Name of the Test? [Name Before '_Data_...'] : ")
#slot = raw_input("> GLIB slot used for the test? [1-12]: ")
#pos  = raw_input("> Position? [0-23]: ")
#port = raw_input("> ID of the VFAT2? : ")

#Number of the channel for which the SCURVE and its fit are printed.
                SCUVRE = 14
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
                #ma = np.zeros(shape=(127,255))
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
                    #ma = np.zeros(shape=(127,255))
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
                                #if "second_threshold" in line:
                                #    break
                                ma[count]=scurvey
                                count = count+1
                                while 0 in scurvey:
                                    scurvey.pop(0)
                                    scurvex.pop(0)
                                while 1 in scurvey:
                                    scurvey.pop(len(scurvey)-1)
                                    scurvex.pop(len(scurvex)-1)
                                    #plt.xlim(min(scurvex),max(scurvex))
                                scurvex2 = []
                                for i in scurvex:
                                    scurvex2.append(i-min(scurvex))
                                if SCName in line:
                                #print str(line)
                                #if line in line:
                                    #if "second_threshold" in line:
                                    #    line = "S_CURVE_" + str(128)
                                    scurvex3 = []
                                    fit=[]

                                    if scurvex2==[]:
                                        print " Error in " + str(SCName)
                                        print len(scurvex)
                                        print len(scurvex2)
                                        
                                    t = np.linspace(min(scurvex2), max(scurvex2), 250)
                                    fitParams, fitCovariances = curve_fit(fitFunc, scurvex2, scurvey)
                                    for i in t:
                                        fit.append(fitFunc(i, fitParams[0], fitParams[1],fitParams[2],fitParams[3]))
                                    #print "---------- Scurve and the erf fit of channel " + str(line) + "-1 in the transition zone ----------"    
                                    print "---------- Scurve and the erf fit of channel " + str(SCUVRE) + " in the transition zone ----------"    
                                    #print str(line) + "-1 ----- " + str(fitParams[0]+min(scurvex)) + " ----- " + str(fitParams[1]) + " ----- " + str(fitParams[2]) + " ----- " + str(fitParams[3])    
                                    plt.xlim(min(scurvex),max(scurvex))
                                    plt.suptitle("%s_VFAT%s_ID_%s_ScurveAndErfFit"%(TestName,pos,port), fontsize=14, fontweight='bold')
                                    plt.plot(scurvex, scurvey,'bo',t+min(scurvex),fit,'r')
                                    #plt.savefig("%s_VFAT%s_ID_%s_ScurveAndErfFit.png"%(TestName,pos,port))
                                    plt.savefig("%s_VFAT%s_ID_%s_14_ScurveAndErfFit.png"%(TestName,pos,port))
                                    #plt.show()
                                    plt.clf()
                                    scurvex3 = []
                                    VCALmean14.append(fitParams[0]+min(scurvex))
                                    VCALcov14.append(fitParams[1])
                                    #print "VCal for channel 14: " + str(mean)
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
                                    #if "second_threshold" in line:
                                    #    line = "S_CURVE_" + str(128)
                                    #print str(line) + "-1 ----- " + str(fitParams[0]+min(scurvex)) + " ----- " + str(fitParams[1]) + " ----- " + str(fitParams[2]) + " ----- " + str(fitParams[3])    
                                except: #If the SCURVE of a channel can not be fit
                                    print "line" + str(line) + "-1 is broken"
                                    mean.append(0) #If the channel is broken, the mean and covariance of the are set to 0
                                    meanALL.append(0)
                                    cov.append(0)
                                    covALL.append(0)
                                if "S_CURVE_128" in line:
                                    #print str(TestName)+"_VFAT"+str(pos)+"_ID_"+str(port)+": mean of the threshold = "+str(meanthreshold/128.)+"; mean of the sigma = "+str(sigmathreshold/128.)
                                    #print str(meanthreshold/128.)
                                    #print str(sigmathreshold/128.)
                                    break
                                if "second_threshold" in line:
                                    Tmean.append(meanthreshold/128.)
                                    Tsigma.append(sigmathreshold/128.)
                                    #print str(TestName)+"_VFAT"+str(pos)+"_ID_"+str(port)+": mean of the threshold = "+str(meanthreshold/128.)+"; mean of the sigma = "+str(sigmathreshold/128.)
                                    #print str(meanthreshold/128.)
                                    #print str(sigmathreshold/128.)
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
                        print("---------- Threshold Scans ----------")    
                        plt.xlim(0,255)
                        plt.ylim(0,100)
                        plt.suptitle("%s_VFAT%s_ID_%s_thresholds"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.plot(threshold1x, threshold1y,'bo',threshold2x, threshold2y,'ro')
                        plt.savefig("%s_VFAT%s_ID_%s_thresholds.png"%(TestName,pos,port))
                        #plt.show() 
                        plt.clf()
                        
                        #Make & store threshold TGraph before Trim
                        gThresh_PreTrim = TGraph(len(threshold1x))
                        gThresh_PreTrim.SetName( "%s_VFAT%s_ID_%s_thresholdsBefore"%(TestName,pos,port) )
                        gThresh_PreTrim.SetLineColor(kBlue)
                        gThresh_PreTrim.SetMarkerColor(kBlue)
                        gThresh_PreTrim.SetMarkerStyle(20)
                        
                        for iPos in range(0,len(threshold1x)):
                            gThresh_PreTrim.SetPoint(iPos,threshold1x[iPos],threshold1y[iPos])
                                
                        dir_Threshold.cd()
                        gThresh_PreTrim.Write()
                        
                        #Make & store threshold TGraph after Trim
                        gThresh_PostTrim = TGraph(len(threshold2x))
                        gThresh_PostTrim.SetName( "%s_VFAT%s_ID_%s_thresholdsAfter"%(TestName,pos,port) )
                        gThresh_PostTrim.SetLineColor(kRed)
                        gThresh_PostTrim.SetMarkerColor(kRed)
                        gThresh_PostTrim.SetMarkerStyle(21)
                            
                        for iPos in range(0,len(threshold2x)):
                            gThresh_PreTrim.SetPoint(iPos,threshold2x[iPos],threshold2y[iPos])
                                
                        dir_Threshold.cd()
                        gThresh_PostTrim.Write()

                        if threshold2x == []:
                            print "Only the TH worked for", str(filename)
                            continue

                        print("---------- Mean of the Erf Function by channel ----------")
                        plt.ylim(0,255)
                        plt.suptitle("%s_VFAT%s_ID_%s_meanerfbychan"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.plot(mean,'bo')
                        plt.savefig("%s_VFAT%s_ID_%s_meanerfbychan.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()
                        
                        #Make & store Mean of Erf by Channel TGraph
                        gErfMeanByChan = TGraph(len(mean))
                        gErfMeanByChan.SetName( "%s_VFAT%s_ID_%s_meanerfbychan"%(TestName,pos,port) )
                        gErfMeanByChan.SetLineColor(kBlue)
                        gErfMeanByChan.SetMarkerColor(kBlue)
                        gErfMeanByChan.SetMarkerStyle(20)
                        
                        for iPos in range(0,len(mean)):
                            gErfMeanByChan.SetPoint(iPos,iPos,mean[iPos])
                        
                        dir_SCurveMeanByChan.cd()
                        gErfMeanByChan.Write()

                        print("---------- cov of the Erf Function by channel ----------")
                        plt.suptitle("%s_VFAT%s_ID_%s_coverfbychan"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.plot(cov,'ro')
                        plt.savefig("%s_VFAT%s_ID_%s_coverfbychan.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()
                        
                        #Make & store Cov of Erf by Channel TGraph
                        gErfCovByChan = TGraph(len(cov))
                        gErfCovByChan.SetName( "%s_VFAT%s_ID_%s_coverfbychan"%(TestName,pos,port) )
                        gErfCovByChan.SetLineColor(kRed)
                        gErfCovByChan.SetMarkerColor(kRed)
                        gErfCovByChan.SetMarkerStyle(20)
                        
                        for iPos in range(0,len(cov)):
                            gErfCovByChan.SetPoint(iPos,iPos,cov[iPos])
                        
                        dir_SCurveCovariance.cd()
                        gErfCovByChan.Write()
                        
                        print("---------- Histogram of the covariance of the Erf Function ----------")
                        plt.hist(cov, 50, normed=1, facecolor='y', alpha = 0.8)
                        plt.suptitle("%s_VFAT%s_ID_%s_covhisterf"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.savefig("%s_VFAT%s_ID_%s_covhisterf.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()
                        
                        #Make & store Cov of Erf by Channel Histogram
                        hCovHistogram = TH1F( "%s_VFAT%s_ID_%s_coverfbychan"%(TestName,pos,port), "", 500,0,250 )
                        
                        for iPos in range(0,len(cov)):
                            hCovHistogram.Fill(cov[iPos])
                        
                        dir_SCurveCovariance.cd()
                        hCovHistogram.Write()
                        
                        #Read and plot the SCurve before the scan
                        fi = glob.glob(str(TestName)+"_SCurve_by_channel_VFAT2_"+str(pos)+"_ID_"+str(port)+"*")[k]
                        g=open(fi)
                                
                                
                        maSC = np.zeros(shape=(128,255))
                        #maSC = np.zeros(shape=(127,255))
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
                        print("---------- S-Curve by channel Before the Script ----------")    
                        plt.suptitle("%s_VFAT%s_ID_%s_scurvebefore"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.imshow(maSC)
                        plt.savefig("%s_VFAT%s_ID_%s_scurvebefore.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()
                        g.close()

                        #Make & store SCurves by Chan No. Before Trimming
                        h2DSCurveByChanPreTrim = TH2F( "%s_VFAT%s_ID_%s_scurvebefore"%(TestName,pos,port), "", 255,0,255, 127, 0, 127)

                        for index, valSCurve in np.ndenumerate(maSC):
                            h2DSCurveByChanPreTrim.SetBinContent(index[1]+1,index[0]+1, valSCurve )
                            
                        dir_SCurveByChan.cd()
                        h2DSCurveByChanPreTrim.Write()

   # Plot the S_Curve after fitting
                        print("---------- S-Curve by channel after the Script ----------")
                        plt.suptitle("%s_VFAT%s_ID_%s_scurveafter"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        plt.imshow(ma)
                        plt.savefig("%s_VFAT%s_ID_%s_scurveafter.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()     

                        #Make & store SCurves by Chan No. Before Trimming
                        h2DSCurveByChanPostTrim = TH2F( "%s_VFAT%s_ID_%s_scurveafter"%(TestName,pos,port), "", 255,0,255, 127, 0, 127)
                            
                        for index, valSCurve in np.ndenumerate(ma):
                            h2DSCurveByChanPostTrim.SetBinContent(index[1]+1,index[0]+1, valSCurve )
                                    
                        dir_SCurveByChan.cd()
                        h2DSCurveByChanPostTrim.Write()

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
                        print("---------- Histogram of the '0.5 point' for a TrimDAC of 0/31 and after the Script ----------")   
                        plt.hist(vcal0, bins=range(min(vcal0), max(vcal0) + 1, 1), normed=1, facecolor='g', alpha = 0.8)
                        
                        line = (f.readline()).rstrip('\n')
                        vcal= line.split()
                        for ele in vcal:
                            if ele.startswith('['):
                                ele = ele[1:]
                            ele = ele.rstrip(']') 
                            ele = ele.rstrip('L,') 
                            vcal31.append(int(ele))
                        
                        plt.hist(vcal31,  bins=range(min(vcal31), max(vcal31) + 1, 1), normed=1, facecolor='r', alpha = 0.8)
                        
                        line = (f.readline())
                        vcal= line.split()
                        for ele in vcal:
                            if ele.startswith('['):
                                ele = ele[1:]
                            ele = ele.rstrip(']') 
                            ele = ele.rstrip('L,') 
                            vcalfinal.append(int(ele))
                        
                        plt.hist(mean,  bins=range(int(min(mean)), int(max(mean)) + 1, 1) , normed=1, facecolor='b', alpha = 0.8)
                        plt.suptitle("%s_VFAT%s_ID_%s_hist05pointafter"%(TestName,pos,port), fontsize=14, fontweight='bold')
                        
                        plt.savefig("%s_VFAT%s_ID_%s_hist05pointafter.png"%(TestName,pos,port))
                        #plt.show()
                        plt.clf()
                        f.close()

#Close Output ROOT File
file_Output.Close()
'''
    print("---------- Mean of the Erf Function for all channels of all chips ----------")
    plt.hist(meanALL, 50, facecolor='b')    
    plt.suptitle("VFAT2 Final VCal Value - All Channels", fontsize=14, fontweight='bold')
    plt.savefig("goodVFAT2meanErfAllChannels.png")
    #plt.show()
    plt.clf()

    print("---------- Mean of the Erf Function for channel 14 of all chips ----------")
    plt.hist(VCALmean14, 50, facecolor='b')    
    plt.suptitle("VFAT2 Final VCal Value - Channel 14", fontsize=14, fontweight='bold')
    plt.savefig("goodVFAT2meanErfChannel14.png")
    #plt.show()
    plt.clf()

    print("---------- Cov of the Erf Function for all channels of all chips ----------")
    plt.hist(covALL, 50, facecolor='b')    
    plt.suptitle("VFAT2 Final S-curve Sigma - All Channels", fontsize=14, fontweight='bold')
    plt.savefig("goodVFAT2sigmaErfAllChannels.png")
    #plt.show()
    plt.clf()

    print("---------- Cov of the Erf Function for channel 14 of all chips ----------")
    plt.hist(VCALcov14, 50, facecolor='b')    
    plt.suptitle("VFAT2 Final S-curve Sigma - Channel 14", fontsize=14, fontweight='bold')
    plt.savefig("goodVFAT2sigmaErfChannel14.png")
    #plt.show()
    plt.clf()

    print("---------- Threshold for all chips ----------")
    plt.hist(thresholdALL, 50, facecolor='b')    
    plt.suptitle("VFAT2 Threshold Value", fontsize=14, fontweight='bold')
    plt.savefig("goodVFAT2threshold.png")
    #plt.show()
    plt.clf()
'''                            
'''
print("---------- Mean of the Erf Function by VFAT ----------")
#plt.ylim(0,6000)
#plt.xlim(0,120)
plt.suptitle("Mean of Final VCal Value - All chips", fontsize=14, fontweight='bold')
plt.hist(Tmean,50,facecolor='b')
plt.savefig("VCal_distribution_by_VFAT.png")
#plt.show()
plt.clf()

print("---------- Mean of the Erf Function by channel ----------")
#plt.ylim(0,6000)
plt.xlim(0,120)
plt.suptitle("VCal distribution by channel", fontsize=14, fontweight='bold')
plt.hist(themean,120)
plt.savefig("VCal_distribution_by_channel.png")
#plt.show()
plt.clf()

print("---------- cov of the Erf Function by channel ----------")
plt.xlim(1.5,5.0)
plt.suptitle("sigma distribution by channel", fontsize=14, fontweight='bold')
plt.hist(thesigma,35)
plt.savefig("sigma_distribution_by_channel.png")
#plt.show()
plt.clf()

print("---------- cov of the Erf Function by VFAT ----------")
plt.xlim(1.5,5.0)
plt.suptitle("sigma distribution by VFAT", fontsize=14, fontweight='bold')
plt.hist(Tsigma,35)
plt.savefig("sigma_distribution_by_VFAT.png")
#plt.show()
plt.clf()
'''
