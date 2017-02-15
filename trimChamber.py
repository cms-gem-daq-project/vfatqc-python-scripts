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

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
print startTime

#run standard tests to check communication with the system
test_params = TEST_PARAMS(nglib=options.nglib,
                          noh=options.noh,
                          ni2c=options.ni2c,
                          ntrk=options.ntrk,
                          writeout=options.writeout)

testSuite = GEMDAQTestSuite(slot=options.slot,
                            gtx=options.gtx,
                            tests=options.tests,
                            test_params=test_params,
                            debug=options.debug)

testSuite.runSelectedTests()
testSuite.report()

dirPath = '%s/%s'%(options.path,startTime)
os.system('mkdir %s'%dirPath)

#bias vfats
biasAllVFATs(testSuite.glib,options.gtx,0x0,enable=False)
writeAllVFATs(testSuite.glib, options.gtx, "VThreshold1", 40, 0)

CHAN_MIN = 0
CHAN_MAX = 128


for vthr1 in range(125,90,-5):
    for trimRange in range(0,5):
        #Set VThreshold1
        writeAllVFATs(testSuite.glib, options.gtx, "VThreshold1", vthr1,0)
        writeAllVFATs(testSuite.glib, options.gtx, "ContReg3", trimRange,0)
        ###############
        # TRIMDAC = 0
        ###############
        #Setting trimdac value
        for vfat in testSuite.presentVFAT2sSingle:
            for scCH in range(CHAN_MIN,CHAN_MAX):
                writeVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1),0)
        
        #Scurve scan with trimdac set to 0
        filename0 = "%s/SCurveData_trimdac0_vthr%i_range%i.root"%(dirPath,vthr1,trimRange)
        os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filename0))
        
        ###############
        # TRIMDAC = 31
        ###############
        #Setting trimdac value
        for vfat in testSuite.presentVFAT2sSingle:
            for scCH in range(CHAN_MIN,CHAN_MAX):
                writeVFAT(testSuite.glib,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH+1),31)
        
        #Scurve scan with trimdac set to 0
        filename31 = "%s/SCurveData_trimdac31_vthr%i_range%i.root"%(dirPath,vthr1,trimRange)
        os.system("python ultraScurve.py -s %s -g %s -f %s"%(options.slot,options.gtx,filename31))
        
        #For each channel, check that the infimum of the scan with trimDAC = 31 is less than the subprimum of the scan with trimDAC = 0. The difference should be greater than the trimdac range.
        muFits_0  = fitScanData(filename0);
        muFits_31 = fitScanData(filename31);
        
        vfat_hist_31 = {}
        vfat_hist_0 = {}
        #vfat0_hist_0 = TH1D("vfat0_hist_0",";Channel Threshold [DAC Units]; Number of Channels",100,0,100)
        for vfat in range(0,24):
            vfat_hist_31[vfat] = TH1D("vfat%i_hist_31"%vfat,";Channel Threshold [DAC Units]; Number of Channels",125,0,250)
            vfat_hist_0[vfat] = TH1D("vfat%i_hist_0"%vfat,";Channel Threshold [DAC Units]; Number of Channels",125,0,250)
            for ch in range(CHAN_MIN,CHAN_MAX):
                #vfat0_hist_0.Fill(muFits_0[0][ch])
                vfat_hist_31[vfat].Fill(muFits_31[vfat][ch])
                vfat_hist_0[vfat].Fill(muFits_0[vfat][ch])
        
        c1 = TCanvas()
        c1.cd()
        
        #vfat0_hist_0.SetFillColor(ROOT.kOrange+1)
        #vfat0_hist_0.Draw()
        for vfat in range(0,24):
            vfat_hist_0[vfat].SetLineColor(ROOT.kRed+2)
            vfat_hist_31[vfat].SetLineColor(ROOT.kGreen+2)
            vfat_hist_0[vfat].SetLineWidth(2)
            vfat_hist_31[vfat].SetLineWidth(2)
            vfat_hist_0[vfat].Draw()
            vfat_hist_31[vfat].Draw("same")
            c1.SaveAs("%s/vfat%i_vthr%i_range%i.png"%(dirPath,vfat,vthr1,trimRange))
        
