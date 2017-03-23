import os
import threading
from chamberInfo import chamber_config,GEBtype

def launchScurveScan(link, filename,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i %s -f -t %s"%(filename,cType))

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,filename,cType]))

for t in threads:
  t.start()


