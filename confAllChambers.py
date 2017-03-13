import os
import threading

def launchScurveScan(link):
  os.system("python confChamber.py -s 3 -g %i"%link)

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
  filename="SCurveData_%s.root"%(chamber_config[link])
  #launchScurveScan(link,filename)
  threads.append(threading.Thread(target=launchScurveScan, args=[link]))
for t in threads:
  t.start()

	
