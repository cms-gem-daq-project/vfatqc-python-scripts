import os
import threading

def launchScurveScan(link, filename,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i %s -f -t %s"%(filename,cType))

threads = []
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
GEBtype = {
  0:"short",
  1:"short",
  2:"short",
  3:"short",
  4:"long",
  5:"long",
  6:"short",
  7:"short",
  8:"long",
  9:"long"
  }

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,filename,cType]))

for t in threads:
  t.start()

	
