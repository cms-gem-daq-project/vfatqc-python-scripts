import os
import threading
from chamberInfo import chamber_config

def launchScurveScan(link):
  os.system("python confChamber.py -s 3 -g %i"%link)

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  #launchScurveScan(link,filename)
  threads.append(threading.Thread(target=launchScurveScan, args=[link]))
for t in threads:
  t.start()


