#!/bin/env python
import os
import threading
from chamberInfo import chamber_config
from qcoptions import parser
from gempython.utils.wrappers import envCheck

parser.add_option("--run", action="store_true", dest="run",
                  help="Set VFATs to run mode", metavar="run")
parser.add_option("--config", action="store_true", dest="config",
                  help="Set Configuration from simple txt files", metavar="config")
parser.add_option("--vt1", type="int", dest="vt1",
                  help="VThreshold1 DAC value for all VFATs", metavar="vt1", default=100)


(options, args) = parser.parse_args()

def launchScurveScan(link,slot,filename,run,vt1,conf,cName,ztrim):
    dataPath = os.getenv('DATA_PATH')
    if conf:
        if run:
            os.system("confChamber.py -s %i -g %i --chConfig %s/configs/z%.1f/chConfig_%s.txt --vfatConfig %s/configs/z%.1f/vfatConfig_%s.txt --run"%(slot,link,dataPath,ztrim,cName,dataPath,ztrim,cName))
            pass
        else:
            os.system("confChamber.py -s %i -g %i --chConfig %s/configs/z%.1f/chConfig_%s.txt --vfatConfig %s/configs/z%.1f/vfatConfig_%s.txt"%(slot,link,dataPath,ztrim,cName,dataPath,ztrim,cName))
            pass
        pass
    else:
        if run:
            os.system("confChamber.py -s %i -g %i --filename %s --run --vt1=%i"%(slot,link,filename,vt1))
            pass
        else:
            os.system("confChamber.py -s %i -g %i --filename %s --vt1=%i"%(slot,link,filename,vt1))
            pass
        pass


threads = []

envCheck('DATA_PATH')

for link in range(10):
    dataPath = os.getenv('DATA_PATH')
    filename="%s/%s/trim/z%f/config/SCurveData_Trimmed/SCurveFitData.root"%(dataPath,chamber_config[link],options.ztrim)
    if os.path.isfile(filename):
      #launchScurveScan(link,filename)
      threads.append(threading.Thread(target=launchScurveScan, args=[link,options.slot,filename,options.run,options.vt1,options.config,chamber_config[link],options.ztrim]))
    else:
      print "No trim configuration exists for z = %f for %s"%(options.ztrim,chamber_config[link])
    pass

for t in threads:
    t.start()
    pass



