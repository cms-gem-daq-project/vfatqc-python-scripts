import os
import threading
from chamberInfo import chamber_config,GEBtype
from qcoptions import parser

(options, args) = parser.parse_args()

def launchScurveScan(link,ztrim,cName,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i /gemdata/%s/scurve/current/SCurveData.root -f -t %s"%(cName,cType))
  os.system("cp /gemdata/%s/scurve/current/SCurveData/Summary.png ~/move/SCurveSummary_%s.png"%(cName,cName))

ztrim = options.ztrim

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  cName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,ztrim,cName,cType]))

for t in threads:
  t.start()


