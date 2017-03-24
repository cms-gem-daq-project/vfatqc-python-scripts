import os
import threading
from chamberInfo import chamber_config,GEBtype
from qcoptions import parser

parser.add_option("--ztrim", type="float", dest="ztrim",
                  help="ztrim of config to load", metavar="ztrim", default=0.0)

(options, args) = parser.parse_args()

def launchScurveScan(link,ztrim,cName,cType):
  os.system("python $BUILD_HOME/vfatqc-python-scripts/macros/anaUltraScurve.py -i data/%s/trimming/z%f/current/SCurveData_trimdac0_range0.root -f -t %s"%(cName,ztrim,cType))

ztrim = options.ztrim

threads = []

for link in range(10):
  filename="SCurveData_%s.root"%(chamber_config[link])
  cType = GEBtype[link]
  cName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,ztrim,cName,cType]))

for t in threads:
  t.start()


