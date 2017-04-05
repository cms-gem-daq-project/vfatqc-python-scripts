import os
import threading
from chamberInfo import chamber_config,GEBtype
from qcoptions import parser

(options, args) = parser.parse_args()

if os.getenv('DATA_PATH') == None or os.getenv('DATA_PATH') == '':
  print 'You must source the environment properly, DATA_PATH is not set'
  exit(0)
if os.getenv('CONFIG_PATH') == None or os.getenv('CONFIG_PATH') == '':
  print 'You must source the environment properly, CONFIG_PATH is not set'
  exit(0)
if os.getenv('BUILD_HOME') == None or os.getenv('BUILD_HOME') == '':
  print 'You must source the environment properly, BUILD_HOME is not set'
  exit(0)


def launchScurveScan(link,ztrim,cName,cType):
  import ROOT as r
  buildPath = os.getenv('BUILD_PATH')
  dataPath = os.getenv('DATA_PATH')
  configPath = os.getenv('CONFIG_PATH')
  trimFile = r.TFile( '%s/%s/trim/z%f/config/SCurveData_Trimmed.root'%(dataPath,cName,ztrim) )
  trimRange = {}
  outTrimFile = open('%s/chConf%s.txt'%(configPath,cName),'w')
  outTrimFile.write('vfatN\I:vfatCH\I:trimDAC\I\n')
  for event in trimFile.scurveTree :
    if event.vcal == 10 :
      outTrimFile.write('%i\t%i\t%i\n'%(int(event.vfatN),int(event.vfatCH),int(event.trimDAC)))
      if event.vfatCH == 10 : trimRange[int(event.vfatN)] = int(event.trimRange)
  outTrimFile.close()
  trimFile.Close()
  os.system( 'cp %s/%s/threshold/config/ThresholdScanData/ThresholdByVFAT.txt %s/vthConf%s.txt'%(dataPath,cName,configPath,cName) )

ztrim = options.ztrim

threads = []

for link in range(10):
  cType = GEBtype[link]
  cName = chamber_config[link]
  threads.append(threading.Thread(target=launchScurveScan, args=[link,ztrim,cName,cType]))

for t in threads:
  t.start()


