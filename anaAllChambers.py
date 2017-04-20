#!/bin/env python

import os
import threading
from chamberInfo import chamber_config,GEBtype
from qcoptions import parser

def launchScurveScan(link,scandate,cName,cType,ztrim):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i /gemdata/%s/scurve/%s/SCurveData.root -f -t %s"%(cName,scandate,cType))
  os.system("cp /gemdata/%s/scurve/%s/SCurveData/Summary.png ~/move/SCurveSummary_%s_ztrip%2.2f.png"%(cName,scandate,cName,ztrim))

parser.add_option("--scandate", type="string", dest="scandate", default="current",
                  help="Specify specific date to analyze", metavar="scandate")

(options, args) = parser.parse_args()

ztrim = options.ztrim

import glob
searchPath = "%s/GEMINI*/scurve/*"%(os.getenv('DATA_PATH'))
dirs = glob.glob(searchPath)
foundDir = False
for path in dirs:
  if path.rfind(options.scandate) > 0:
    foundDir = True
if not foundDir:
  print "Unable to find %s in output location specified: %s"%(options.scandate,searchPath)
  exit(50)
else:
  print "Found %s"%(options.scandate)

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  cName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,options.scandate,cName,cType,ztrim]))

for t in threads:
  t.start()
