import os
import threading
from chamberInfo import chamber_config

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
    filename="%s/%s/trimming/z0.000000/config/SCurveData_Trimmed.root"%(dataPath,chamber_config[link])
    #launchScurveScan(link,filename)
    threads.append(threading.Thread(target=launchScurveScan, args=[link,filename]))
    pass

for t in threads:
    t.start()
    pass



