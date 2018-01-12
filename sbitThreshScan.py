from cmd import Cmd
import sys, os, subprocess
from rw_reg import *
import time

class Colors:
    WHITE   = '\033[97m'
    CYAN    = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE    = '\033[94m'
    YELLOW  = '\033[93m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    ENDC    = '\033[0m'

def printCyan(string):  
    print Colors.CYAN  
    print string, Colors.ENDC

def printGreen(string):
    print Colors.GREEN
    print string, Colors.ENDC
                          
def printRed(string):
    print Colors.RED
    print string, Colors.ENDC

NOISE_CHECK_SLEEP = 0.001

vfatN = 20
nInj  = 100

if __name__ == '__main__':
#    try:
        if (len(sys.argv) < 3):
            print "usage:"
            print "python sbitThreshScan.py [VFATN] [0 -> ARM; 1 -> ZCC]"
            exit(0)
        else:
            vfatN = int(sys.argv[1])
            isZCC = int(sys.argv[2])
        
        print "Testing VFAT%i" % vfatN
        print "isZCC: %i" % isZCC

        parseXML()

        print "Threshold,rate"
        scanReg = "CFG_THR_ARM_DAC"
        if isZCC:
            scanReg = "CFG_THR_ZCC_DAC"

        for thresh in range(0, 256, 2):
            writeReg(getNode(("GEM_AMC.OH.OH0.GEB.VFAT%i.%s")%(vfatN,scanReg)), thresh)
            time.sleep(3)
            print "%i, %i" % (thresh, int(readReg(getNode("GEM_AMC.TRIGGER.OH0.TRIGGER_RATE")), 0))

