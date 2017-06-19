import os
import threading
from chamberInfo import chamber_config

def launchScurveScan(link,trimName):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/trimChamber.py -s3 -g %i -p 0.0 --trimRange data/jaredTrim/%s/SCurveData_trimdac31_range4.root &> log/trim%i.log"%(link,trimName,link))

threads = []

for link in range(10):
  #if (link == 6 or link == 8): continue
  #launchScurveScan(link,filename)
  trimName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,trimName]))
for t in threads:
  t.start()

	
