#!/bin/env python
"""
Script to set trimdac values on a chamber
By: Christine McLean (ch.mclean@cern.ch), Cameron Bravo (c.bravo@cern.ch), Elizabeth Starling (elizabeth.starling@cern.ch)
"""

import sys, os, random, time
from array import array
from GEMDAQTestSuite import *
from vfat_functions_uhal import *
from optparse import OptionParser
from ROOT import TFile,TTree,TH1D,TCanvas,gROOT,gStyle,TF1
from fitScanData import fitScanData
import ROOT

parser = OptionParser()

parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot", default=10)
parser.add_option("--shelf", type="int", dest="shelf",
                  help="The uTCA crate", metavar="shelf", default=1)
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the GLIB", metavar="gtx", default=0)
parser.add_option("--nglib", type="int", dest="nglib",
                  help="Number of register tests to perform on the glib (default is 100)", metavar="nglib", default=100)
parser.add_option("--noh", type="int", dest="noh",
                  help="Number of register tests to perform on the OptoHybrid (default is 100)", metavar="noh", default=100)
parser.add_option("--ni2c", type="int", dest="ni2c",
                  help="Number of I2C tests to perform on the VFAT2s (default is 100)", metavar="ni2c", default=100)
parser.add_option("--ntrk", type="int", dest="ntrk",
                  help="Number of tracking data packets to readout (default is 100)", metavar="ntrk", default=100)
parser.add_option("--writeout", action="store_true", dest="writeout",
                  help="Write the data to disk when testing the rate", metavar="writeout")
parser.add_option("--tests", type="string", dest="tests",default="A,B,C,D,E",
                  help="Tests to run, default is all", metavar="tests")
parser.add_option("--path", type="string", dest="path", default="data",
                  help="Specify Output File Path", metavar="path")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

(options, args) = parser.parse_args()

chamber_config = {
  0:"SC1L1",
  1:"SC1L2",
  2:"SC27L1",
  3:"SC27L2",
  4:"SC28L1",
  5:"SC28L2",
  6:"SC29L1",
  7:"SC29L2",
  8:"SC30L1",
  9:"SC30L2"
  }


import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime

connection_file = "file://${GEM_ADDRESS_TABLE_PATH}/connections.xml"
manager         = uhal.ConnectionManager(connection_file )
amc  = manager.getDevice( "gem.shelf%02d.amc%02d.optohybrid%02d"%(options.shelf,options.slot,options.gtx) )

dirPath = '%s/trim%s'%(options.path,chamber_config[options.gtx])
os.system('mkdir %s'%dirPath)

#bias vfats
biasAllVFATs(amc,options.gtx,0x0,enable=False)
writeAllVFATs(amc, options.gtx, "VThreshold1", 100, 0)

CHAN_MIN = 0
CHAN_MAX = 128

masks = {}
for vfat in range(0,24):
    masks[vfat] = {}
    for ch in range(CHAN_MIN,CHAN_MAX):
        masks[vfat][ch] = False

#Find trimRange for each VFAT
tRanges = {}
tRangeGood = {}
trimVcal = {}
goodSup = {}
goodInf = {}
for vfat in range(0,24):
    tRanges[vfat] = 0
    tRangeGood[vfat] = False
    trimVcal[vfat] = 0
    goodSup[vfat] = -99
    goodInf[vfat] = -99

###############
# TRIMDAC = 0
###############
#Configure for initial scan
for vfat in range(0,24):
    writeVFAT(amc, options.gtx, vfat, "ContReg3", tRanges[vfat],0)
    for scCH in range(CHAN_MIN,CHAN_MAX):
        writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),0)
#Scurve scan with trimdac set to 0
filename0 = "%s/SCurveData_trimdac0_range0.root"%dirPath
os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filename0))
muFits_0  = fitScanData(filename0)
    

#This loop determines the trimRangeDAC for each VFAT
for trimRange in range(0,5):
    #Set Trim Ranges
    for vfat in range(0,24):
        writeVFAT(amc, options.gtx, vfat, "ContReg3", tRanges[vfat],0)
    ###############
    # TRIMDAC = 31
    ###############
    #Setting trimdac value
    for vfat in range(0,24):
        for scCH in range(CHAN_MIN,CHAN_MAX):
            writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),31)
    
    #Scurve scan with trimdac set to 31 (maximum trimming)
    filename31 = "%s/SCurveData_trimdac31_range%i.root"%(dirPath,trimRange)
    os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filename31))
    
    #For each channel, check that the infimum of the scan with trimDAC = 31 is less than the subprimum of the scan with trimDAC = 0. The difference should be greater than the trimdac range.
    muFits_31 = fitScanData(filename31)
    
    sup = {}
    supCH = {}
    inf = {}
    infCH = {}
    #Check to see if the new trimRange is good
    for vfat in range(0,24):
        if(tRangeGood[vfat]): continue
        sup[vfat] = 999.0
        inf[vfat] = 0.0
        supCH[vfat] = -1
        infCH[vfat] = -1
        for ch in range(CHAN_MIN,CHAN_MAX):
            if(masks[vfat][ch]): continue
            #if(muFits_31[0][vfat][ch] - 4*muFits_31[1][vfat][ch] > inf[vfat]): 
            if(muFits_31[0][vfat][ch]  > inf[vfat]): 
                inf[vfat] = muFits_31[0][vfat][ch]
                #inf[vfat] = muFits_31[0][vfat][ch] - 4*muFits_31[1][vfat][ch]
                infCH[vfat] = ch
            #if(muFits_0[0][vfat][ch] - 4*muFits_0[1][vfat][ch] < sup[vfat] and muFits_0[0][vfat][ch] - 4*muFits_0[1][vfat][ch] > 0.1): 
            if(muFits_0[0][vfat][ch] < sup[vfat] and muFits_0[0][vfat][ch] > 0.1): 
                sup[vfat] = muFits_0[0][vfat][ch]
                #sup[vfat] = muFits_0[0][vfat][ch] - 4*muFits_0[1][vfat][ch]
                supCH[vfat] = ch
        print "vfat: %i"%vfat
        print muFits_0[0][vfat]
        print muFits_31[0][vfat]
        print "sup: %f  inf: %f"%(sup[vfat],inf[vfat])
        print "supCH: %f  infCH: %f"%(supCH[vfat],infCH[vfat])
        print " "
        if(inf[vfat] <= sup[vfat]):
            tRangeGood[vfat] = True
            goodSup[vfat] = sup[vfat]
            goodInf[vfat] = inf[vfat]
            trimVcal[vfat] = sup[vfat]
        else:
            tRanges[vfat] += 1
            trimVcal[vfat] = sup[vfat]

#Init trimDACs to all zeros
trimDACs = {}
for vfat in range(0,24):
    trimDACs[vfat] = {}
    for ch in range(CHAN_MIN,CHAN_MAX):
        trimDACs[vfat][ch] = 0

#This is a binary search to set each channel's trimDAC
for i in range(0,5):
    #First write this steps values to the VFATs
    for vfat in range(0,24):
        for ch in range(CHAN_MIN,CHAN_MAX):
            trimDACs[vfat][ch] += pow(2,4-i)
            writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(ch+1),trimDACs[vfat][ch])
    #Run an SCurve
    filenameBS = "%s/SCurveData_binarySearch%i.root"%(dirPath,i)
    os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filenameBS))
    #Fit Scurve data
    fitData = fitScanData(filenameBS)
    #Now use data to determine the new trimDAC value
    for vfat in range(0,24):
        for ch in range(CHAN_MIN,CHAN_MAX):
            if(fitData[0][vfat][ch] < trimVcal[vfat]): trimDACs[vfat][ch] -= pow(2,4-i)
            #if(fitData[0][vfat][ch] - 4*fitData[1][vfat][ch] < trimVcal[vfat]): trimDACs[vfat][ch] -= pow(2,4-i)

#Now take a scan with trimDACs found by binary search
for vfat in range(0,24):
    for ch in range(CHAN_MIN,CHAN_MAX):
        writeVFAT(amc,options.gtx,vfat,"VFATChannels.ChanReg%d"%(ch+1),trimDACs[vfat][ch])

filenameFinal = "%s/SCurveData_Trimmed.root"%dirPath
os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filenameFinal))
    
scanFilename = '%s/scanInfo.txt'%dirPath
outF = open(scanFilename,'w')
outF.write('vfat/I:tRange/I:sup/D:inf/D:trimVcal/D')
for vfat in range(0,24):
    outF.write('%i  %i  %f  %f  %f\n'%(vfat,tRanges[vfat],goodSup[vfat],goodInf[vfat],trimVcal[vfat]))
   
outF.close()






















