import os
import threading
from chamberInfo import chamber_config,GEBtype

def launchScurveScan(link, cName,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i data/%s/trimming/p_0.000000/current/SCurveData_trimdac0_range0.root -f -t %s"%(cName,cType))

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  cName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,cName,cType]))

for t in threads:
  t.start()


