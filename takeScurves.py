#!/bin/env python
"""
Script for shifter to use to take scurve data at p5
By: Cameron Bravo (c.bravo@cern.ch)
"""

import sys, os, random, time
from array import array
from optparse import OptionParser

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
startTime = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S.%f")
print startTime

if os.getenv('DATA_PATH') == None or os.getenv('DATA_PATH') == '':
    print 'You must source the environment properly!'
if os.getenv('BUILD_HOME') == None or os.getenv('BUILD_HOME') == '':
    print 'You must source the environment properly!'

for link in range(0,10):
    dirPath = '$DATA_PATH/%s/scurves/%s'%(chamber_config[link],startTime)
    os.system('mkdir -p %s'%dirPath)
    os.system("python $BUILD_HOME/vfatqc-python-scripts/confChamber.py -s3 -g %i"%link)
    os.system("python $BUILD_HOME/vfatqc-python-scripts/ultraScurve.py -s3 -g %i -f %s/SCurveData.root 2>&1 | tee %s/ultraScurve.log"%(link,dirPath,dirPath))






