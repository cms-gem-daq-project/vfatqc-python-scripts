#!/bin/env python
"""
Script for shifter to use to take scurve data at p5
By: Cameron Bravo (c.bravo@cern.ch)
"""

import sys, os, random, time
from chamberInfo import chamber_config
from qcoptions import parser
from gempython.utils.wrappers import envCheck

(options, args) = parser.parse_args()

import subprocess,datetime
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime

envCheck('DATA_PATH')
envCheck('BUILD_HOME')

for link in range(0,10):
    dirPath = '$DATA_PATH/%s/scurves/%s'%(chamber_config[link],startTime)
    os.system('mkdir -p %s'%dirPath)
    #os.system("python $BUILD_HOME/vfatqc-python-scripts/confChamber.py -s3 -g %i"%link)
    os.system("python $BUILD_HOME/vfatqc-python-scripts/ultraScurve.py -s3 -g %i -f %s/SCurveData.root 2>&1 | tee %s/ultraScurve.log"%(link,dirPath,dirPath))






