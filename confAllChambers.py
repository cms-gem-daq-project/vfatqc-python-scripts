import os
import threading
from chamberInfo import chamber_config
from qcoptions import parser

parser.add_option("--run", action="store_true", dest="run",
                  help="Set VFATs to run mode", metavar="run")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)


(options, args) = parser.parse_args()

def launchScurveScan(link,filename,run,vt1):
    if run:
        os.system("confChamber.py -s 3 -g %i --filename %s --run --vt1=%i"%(link,filename,vt1))
    else:
        os.system("confChamber.py -s 3 -g %i --filename %s --vt1=%i"%(link,filename,vt1))

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
    filename="%s/%s/trim/z%f/config/SCurveData_Trimmed.root"%(dataPath,chamber_config[link],options.ztrim)
    if os.path.isfile(filename):
      #launchScurveScan(link,filename)
      threads.append(threading.Thread(target=launchScurveScan, args=[link,filename,options.run,vt1]))
    else:
      print "No trim configuration exists for z = %f for %s"%(options.ztrim,chamber_config[link])
    pass

for t in threads:
    t.start()
    pass



