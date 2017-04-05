#!/bin/env python
"""
Script for shifter to use to take scurve data at p5
By: Cameron Bravo (c.bravo@cern.ch)
"""

import sys, os, random, time
from chamberInfo import chamber_config
from qcoptions import parser

(options, args) = parser.parse_args()

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






