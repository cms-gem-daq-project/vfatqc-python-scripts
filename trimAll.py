import os
import threading
from chamberInfo import chamber_config

def launchScurveScan(link):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/trimChamber.py -s3 -g %i -p 0.0 &> log/trim%i.log"%(link,link))

threads = []

for link in range(10):
  #if (link == 6 or link == 8): continue
  #launchScurveScan(link,filename)
  threads.append(threading.Thread(target=launchScurveScan, args=[link]))
for t in threads:
  t.start()

	
