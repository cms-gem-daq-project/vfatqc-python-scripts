#!/bin/env python2.7

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 09:29:24 2016

@author: Hugo
@modifiedby: Jared
"""
import matplotlib.pyplot as plt
import scipy
from scipy import special
from scipy.optimize import curve_fit
import numpy as np
import glob
choose = glob.glob("*Data_GLIB_IP_192*")
print 
print "---------------- List Of the Files --------------"
print choose
TestName = raw_input("> Name of the Test? [Name Before '_Data_...'] : ")
slot = raw_input("> GLIB slot used for the test? [1-12]: ")
pos  = raw_input("> Position? [0-23]: ")
port = raw_input("> ID of the VFAT2? : ")

#Number of the channel for which the SCURVE and its fit are printed.
SCUVRE = 14


threshold1x = []
threshold1y = []
scurvex = []
scurvey = []
threshold2x = []
threshold2y = []
mean = []
cov = []
ma = np.zeros(shape=(127,255))
count=0
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
    ma = np.zeros(shape=(127,255))
    count=0
    print
    f=open(filename)

    line = (f.readline()).rstrip('\n')
    print
    print line
    print
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
                if "second_threshold" in line:
                    break
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
                    scurvex3 = []
                    fit=[]
                    t = np.linspace(min(scurvex2), max(scurvex2), 250)
                    fitParams, fitCovariances = curve_fit(fitFunc, scurvex2, scurvey)
                    for i in t:
                        fit.append(fitFunc(i, fitParams[0], fitParams[1],fitParams[2],fitParams[3]))
                    print "---------- Scurve and the erf fit of channel " + str(SCUVRE) + " in the transition zone ----------"    
                    plt.xlim(min(scurvex),max(scurvex))
                    plt.plot(scurvex, scurvey,'bo',t+min(scurvex),fit,'r')
                    plt.show()
                    scurvex3 = []
                if scurvey==[]: #If the SCURVE of a channel was only 1 or 0
                    print "line " + str(line) + "-1 is broken"
                    mean.append(0) #If the channel is broken, the mean and covariance of the are set to 0
                    cov.append(0)
                    scurvex = []
                    scurvey = []
                    scurvex2 = []
                    line = (f.readline()).rstrip('\n')
                    continue
                try: # Fit the SCurve with the erf function
                    fitParams, fitCovariances = curve_fit(fitFunc, scurvex2, scurvey)
                    mean.append(fitParams[0]+min(scurvex))
                    cov.append(fitParams[1])
                except: #If the SCURVE of a channel can not be fit
                    print "line" + str(line) + "-1 is broken"
                    mean.append(0) #If the channel is broken, the mean and covariance of the are set to 0
                    cov.append(0)
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
        plt.plot(threshold1x, threshold1y,'bo',threshold2x, threshold2y,'ro')
        plt.show() 
        plt.savefig("%s_VFAT%s_ID%s_thresholds.png"%(TestName,pos,port))
        if threshold2x == []:
            print "Only the TH worked for", str(filename)
            continue

        print("---------- Mean of the Erf Function by channel ----------")
        plt.ylim(0,255)
        plt.plot(mean,'bo')
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_meanerfbychan.png"%(TestName,pos,port))
        plt.clf()
        
        print("---------- cov of the Erf Function by channel ----------")
        plt.plot(cov,'ro')
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_coverfbychan.png"%(TestName,pos,port))
        plt.clf()
        
        print("---------- Histogram of the covariance of the Erf Function ----------")
        plt.hist(cov, 50, normed=1, facecolor='y', alpha = 0.8)
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_covhisterf.png"%(TestName,pos,port))
        plt.clf()
        
#Read and plot the SCurve before the scan       
        fi = glob.glob(str(TestName)+"_SCurve_by_channel_VFAT2_"+str(pos)+"_ID_"+str(port)+"*")[k]
        g=open(fi)
                
                
        maSC = np.zeros(shape=(127,255))
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
        plt.imshow(maSC)
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_scurvebefore.png"%(TestName,pos,port))
        plt.clf()
        g.close()
        
   # Plot the S_Curve after fitting
        print("---------- S-Curve by channel after the Script ----------")
        plt.imshow(ma)
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_scurveafter.png"%(TestName,pos,port))
        plt.clf()     
        
    
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
        
        plt.show()
        plt.savefig("%s_VFAT%s_ID%s_hist05pointafter.png"%(TestName,pos,port))
        plt.clf()
        f.close()
