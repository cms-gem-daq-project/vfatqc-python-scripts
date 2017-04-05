import os
import threading
from chamberInfo import chamber_config,GEBtype
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-r", "--run", type="string", dest="runname", default="2017.03.15-15.03.49.081532",
                  help="Specify Run to Process", metavar="runname")

(options, args) = parser.parse_args()

def launchAnaScurve(filename,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i %s -f -t %s"%(filename,cType))

threads = []

for link in range(10):
  dirPath = 'data/%s/scurves/%s'%(chamber_config[link],options.runname)
  filename="%s/SCurveData.root"%dirPath
  cType = GEBtype[link]
  threads.append(threading.Thread(target=launchAnaScurve, args=[filename,cType]))

for t in threads:
  t.start()


