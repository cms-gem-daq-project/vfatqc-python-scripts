import os
import threading

def launchScurveScan(link, filename):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/confChamber.py -s3 -g %i"%link)
  os.system("python $BUILD_HOME/vfatqc-python-scripts/ultraScurve.py -s3 -g %i -f %s > %s.log"%(link,filename,filename[:-5]))

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

for link in range(10):
  if not (link == 6 or link == 8): continue
  filename="SCurveData_%s.root"%(chamber_config[link])
  launchScurveScan(link,filename)
  #threads.append(threading.Thread(target=launchScurveScan, args=[link, filename]))
#for t in threads:
#  t.start()

	
