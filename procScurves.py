import os
import threading
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-r", "--run", type="string", dest="runname", default="2017.03.15-15.03.49.081532",
                  help="Specify Run to Process", metavar="runname")

(options, args) = parser.parse_args()

def launchAnaScurve(filename,cType):
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
  dirPath = 'data/%s/scurves/%s'%(chamber_config[link],options.runname)
  filename="%s/SCurveData.root"%dirPath
  cType = GEBtype[link]
  threads.append(threading.Thread(target=launchAnaScurve, args=[filename,cType]))

for t in threads:
  t.start()

	
