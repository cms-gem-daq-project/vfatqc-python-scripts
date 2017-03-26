import os
import threading
from chamberInfo import chamber_config
from qcoptions import parser

parser.add_option("--ztrim", type="float", dest="ztrim", default=0.0,
                  help="Specify the p value of the trim", metavar="ztrim")

(options, args) = parser.parse_args()

def launchScurveScan(link,filename):
    os.system("python confChamber.py -s 3 -g %i --filename %s"%(link,filename))

threads = []
if os.getenv('DATA_PATH') == None or os.getenv('DATA_PATH') == '':
    print 'You must source the environment properly!'
    exit(0)
    pass

if os.getenv('BUILD_HOME') == None or os.getenv('BUILD_HOME') == '':
    print 'You must source the environment properly!'
    exit(0)
    pass

for link in range(10):
    dataPath = os.getenv('DATA_PATH')
    filename="%s/%s/trimming/z%f/config/SCurveData_Trimmed.root"%(dataPath,chamber_config[link],options.ztrim)
    if os.path.isfile(filename):
      #launchScurveScan(link,filename)
      threads.append(threading.Thread(target=launchScurveScan, args=[link,filename]))
    else:
      print "No trim configuration exists for z = %f for %s"%(options.ztrim,chamber_config[link])
    pass

for t in threads:
    t.start()
    pass



