import os
import threading

def launchScurveScan(link,trimName):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/trimChamber.py -s3 -g %i -p 0.0 --trimRange data/jaredTrim/%s/SCurveData_trimdac31_range4.root &> log/trim%i.log"%(link,trimName,link))

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

trim_name = {
  0:"GEMINI01L1",
  1:"GEMINI01L2",
  2:"GEMINI27L1",
  3:"GEMINI27L2",
  4:"GEMINI28L1",
  5:"GEMINI28L2",
  6:"GEMINI29L1",
  7:"GEMINI29L2",
  8:"GEMINI30L1",
  9:"GEMINI30L2"
  }

for link in range(10):
  #if (link == 6 or link == 8): continue
  #launchScurveScan(link,filename)
  trimName = trim_name[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,trimName]))
for t in threads:
  t.start()

	
