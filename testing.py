#!/usr/bin/env python

import sys, os, random, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/kernel")

sys.path.append('${GEM_PYTHON_PATH}')

import uhal
from registers_uhal import *
from glib_system_info_uhal import *
from rate_calculator import rateConverter,errorRate
from glib_user_functions_uhal import *
from optohybrid_user_functions_uhal import *
#from vfat_user_functions_uhal import *

####################################################

print
print "This python script will test the GLIB, optical links, OH, and VFAT2 functionalities."
print "Simply follow the instructions on the screen in order to diagnose the setup."
print "Thomas Lenzi - tlenzi@ulb.ac.be"
print

####################################################

Passed = '\033[92m   > Passed... \033[0m'
Failed = '\033[91m   > Failed... \033[0m'

def txtTitle(str):
    print '\033[1m' + str + '\033[0m'


print

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s", "--slot", type="int", dest="slot",
                  help="slot in uTCA crate", metavar="slot", default=10)
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the GLIB", metavar="gtx", default=0)
parser.add_option("--nglib", type="int", dest="nglib",
                  help="Number of register tests to perform on the glib (default is 100)", metavar="nglib", default=100)
parser.add_option("--noh", type="int", dest="noh",
                  help="Number of register tests to perform on the OptoHybrid (default is 100)", metavar="noh", default=100)
parser.add_option("--ni2c", type="int", dest="ni2c",
                  help="Number of I2C tests to perform on the VFAT2s (default is 100)", metavar="ni2c", default=100)
parser.add_option("--ntrk", type="int", dest="ntrk",
                  help="Number of tracking data packets to readout (default is 100)", metavar="ntrk", default=100)
parser.add_option("--writeout", action="store_true", dest="writeout",
                  help="Write the data to disk when testing the rate", metavar="writeout")

parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")

(options, args) = parser.parse_args()

GLIB_REG_TEST = options.nglib
OH_REG_TEST   = options.noh
I2C_TEST      = options.ni2c
TK_RD_TEST    = options.ntrk
RATE_WRITE    = options.writeout

uhal.setLogLevelTo( uhal.LogLevel.FATAL )

uTCAslot = 170
if options.slot:
    uTCAslot = 160+options.slot

if options.debug:
    print options.slot, uTCAslot

ipaddr = '192.168.0.%d'%(uTCAslot)

address_table = "file://${GEM_ADDRESS_TABLE_PATH}/glib_address_table.xml"
uri = "chtcp-2.0://localhost:10203?target=%s:50001"%(ipaddr)
glib       = uhal.getDevice( "glib" , uri, address_table )
oh_basenode = "GLIB.OptoHybrid_%d.OptoHybrid"%(options.gtx)

####################################################

txtTitle("A. Testing the GLIB's presence")
print "   Trying to read the GLIB board ID... If this test fails, the script will stop."

if (readRegister(glib,"GLIB.SYSTEM.BOARD_ID") != 0):
    print Passed
else:
    print Failed
    sys.exit()

testA = True

print

####################################################

txtTitle("B. Testing the OH's presence")
print "   Trying to set the OptoHybrid registers... If this test fails, the script will stop."

setReferenceClock(glib,options.gtx, 1)
setTriggerSource(glib, options.gtx, 1)
## added from pythonScript setup
writeRegister(glib,"%s.CONTROL.THROTTLE"%(oh_basenode), 0)


if (getTriggerSource(glib, options.gtx) == 1):
    print Passed
else:
    print Failed, "oh_trigger_source %d"%(getTriggerSource(glib, options.gtx))
    sys.exit()
    pass

if (getReferenceClock(glib,options.gtx) == 1):
    print Passed
else:
    print Failed, "oh_clk_src %d"%(getReferenceClock(glib,options.gtx))
    sys.exit()
    pass

testB = True

print

####################################################

txtTitle("C. Testing the GLIB registers")
print "   Performing single reads on the GLIB counters and ensuring they increment."

countersSingle = []
countersTest = True

for i in range(0, GLIB_REG_TEST):
    countersSingle.append(readRegister(glib,"GLIB.COUNTERS.IPBus.Strobe.Counters"))
    pass

for i in range(1, GLIB_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
        countersTest = False
        pass
    pass
if (countersTest):
    print Passed
else: 
    print Failed
    pass

testC = countersTest

print

####################################################

txtTitle("D. Testing the OH registers")
print "   Performing single reads on the OptoHybrid counters and ensuring they increment."

countersSingle = []
countersTest = True

##### probable failure
for i in range(0, OH_REG_TEST):
    countersSingle.append(readRegister(glib,"%s.COUNTERS.WB.MASTER.Strobe.GTX"%(oh_basenode)))
    pass

for i in range(1, OH_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
        countersTest = False
        pass
    pass

if (countersTest):
    print Passed
else:
    print Failed
    pass

testD = countersTest

print

####################################################

txtTitle("E. Detecting the VFAT2s over I2C")
print "   Detecting VFAT2s on the GEM by reading out their chip ID."

presentVFAT2sSingle = []
presentVFAT2sFifo = []

writeRegister(glib,"%s.GEB.Broadcast.Reset"%(oh_basenode), 0)
readRegister(glib,"%s.GEB.Broadcast.Request.ChipID0"%(oh_basenode))
chipIDs = readBlock(glib,"%s.GEB.Broadcast.Results"%(oh_basenode), 24)

for i in range(0, 24):
    # missing VFAT shows 0x0003XX00 in I2C broadcast result
    #                    0x05XX0800
    # XX is slot number
    # so if ((result >> 16) & 0x3) == 0x3, chip is missing
    # or if ((result) & 0x30000)   == 0x30000, chip is missing
    if (((readRegister(glib,"%s.GEB.VFATS.VFAT%d.ChipID0"%(oh_basenode,i)) >> 24) & 0x5) != 0x5):
        presentVFAT2sSingle.append(i)
        pass
    if (((chipIDs[i] >> 16)  & 0x3) != 0x3):
        presentVFAT2sFifo.append(i)
        pass
    pass
if (presentVFAT2sSingle == presentVFAT2sFifo):
    Passed
    pass
else:
    Failed
    pass

testE = True

print "   Detected", str(len(presentVFAT2sSingle)), "VFAT2s:", str(presentVFAT2sSingle)
print

####################################################

txtTitle("F. Testing the I2C communication with the VFAT2s")
print "   Performing random read/write operation on each connect VFAT2."

testF = True

for i in presentVFAT2sSingle:
    validOperations = 0
    for j in range(0, I2C_TEST):
        writeData = random.randint(0, 255)
        writeRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg3"%(oh_basenode,i), writeData)
        readData = readRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg3"%(oh_basenode,i)) & 0xff
        if (readData == writeData):
            validOperations += 1
            pass
        pass
    writeRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg3"%(oh_basenode,i), 0)
    if (validOperations == I2C_TEST): 
        print Passed, "#%d"%(i)
    else:
        print Failed, "#%d received %d, expected %d"%(i, validOperations, I2C_TEST)
        testF = False
        pass
    pass
print

####################################################

txtTitle("G. Reading out tracking data")
print "   Sending triggers and testing if the Event Counter adds up."

writeRegister(glib,"%s.GEB.Broadcast.Reset"%(oh_basenode), 0)
writeRegister(glib,"%s.GEB.Broadcast.Request.ContReg0"%(oh_basenode), 0)

testG = True

for i in presentVFAT2sSingle:
    t1_mode     =  0
    t1_type     =  0
    t1_n        =  TK_RD_TEST
    t1_interval =  400
    writeRegister(glib,"%s.T1Controller.RESET"%(oh_basenode), 1)
    writeRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg0"%(oh_basenode,i), 55)
    writeRegister(glib,"%s.CONTROL.VFAT.MASK"%(oh_basenode), ~(0x1 << i))
    flushTrackingFIFO(glib,options.gtx)

    nPackets = 0
    timeOut = 0
    ecs = []

    sendL1A(glib,options.gtx,t1_interval,t1_n)

    while (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.DEPTH"%(options.gtx)) != 7 * TK_RD_TEST):
        timeOut += 1
        if (timeOut == 10 * TK_RD_TEST):
            break
        pass
    while (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISEMPTY"%(options.gtx)) != 1):
        packets = readBlock(glib,"GLIB.TRK_DATA.OptoHybrid_%d.FIFO"%(options.gtx), 7)
        if (len(packets) == 0):
            print "read data packet length is 0"
            continue
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)
        pass
    writeRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg0"%(oh_basenode,i), 0)

    if (nPackets != TK_RD_TEST):
        print Failed, "#%d received %d, expected %d"%(i, nPackets, TK_RD_TEST)
        raw_input("press enter to continue")
    else:
        followingECS = True
        for j in range(0, TK_RD_TEST - 1):
            if (ecs[j + 1] == 0 and ecs[j] == 255):
                pass
            elif (ecs[j + 1] - ecs[j] != 1):
                followingECS = False
                print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, ecs[j], ecs[j+1])
                pass
            pass
        if (followingECS):
            print Passed, "#" + str(i)
        else:
            print Failed, "#%d received %d, expected %d, noncontinuous ECs"%(i, nPackets, TK_RD_TEST)
            raw_input("press enter to continue")
            testG = False
            pass
        pass
    pass

print

####################################################

txtTitle("H. Reading out tracking data")
print "   Turning on all VFAT2s and looking that all the Event Counters add up."

testH = True

if (testG):
    writeRegister(glib,"%s.GEB.Broadcast.Reset"%(oh_basenode), 0)
    writeRegister(glib,"%s.GEB.Broadcast.Request.ContReg0"%(oh_basenode), 55)

    mask = 0
    for i in presentVFAT2sSingle:
        mask |= (0x1 << i)
        pass
    writeRegister(glib,"%s.CONTROL.VFAT.MASK"%(oh_basenode), ~(mask))

    sendResync(glib,options.gtx, 10, 1)

    flushTrackingFIFO(glib,options.gtx)

    t1_mode     =  0
    t1_type     =  0
    t1_n        =  TK_RD_TEST
    t1_interval =  400
    writeRegister(glib,"%s.T1Controller.RESET"%(oh_basenode), 1)

    nPackets = 0
    timeOut = 0
    ecs = []

    sendL1A(glib,options.gtx,t1_interval,t1_n)

    while (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.DEPTH"%(options.gtx)) != len(presentVFAT2sSingle) * TK_RD_TEST):
        timeOut += 1
        if (timeOut == 20 * TK_RD_TEST): break
        pass
    while (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISEMPTY"%(options.gtx)) != 1):
        packets = readBlock(glib,"GLIB.TRK_DATA.OptoHybrid_%d.FIFO"%(options.gtx), 7)
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)
        pass
    writeRegister(glib,"%s.GEB.Broadcast.Reset"%(oh_basenode), 0)
    writeRegister(glib,"%s.GEB.Broadcast.Request.ContReg0"%(oh_basenode), 0)

    if (nPackets != len(presentVFAT2sSingle) * TK_RD_TEST):
        print Failed, "#%d received: %d, expected: %d"%(i,nPackets, len(presentVFAT2sSingle) * TK_RD_TEST)
    else:
        followingECS = True
        for i in range(0, TK_RD_TEST - 1):
            for j in range(0, len(presentVFAT2sSingle) - 1):
                if (ecs[i * len(presentVFAT2sSingle) + j + 1] != ecs[i * len(presentVFAT2sSingle) + j]):
                    print "\033[91m   > #%d saw %d, %d saw %d \033[0m"%(j+1, ecs[i * len(presentVFAT2sSingle) + j + 1],
                                                                        j, ecs[i * len(presentVFAT2sSingle) + j])
                    followingECS = False
                    pass
                pass
            if (ecs[(i + 1) * len(presentVFAT2sSingle)]  == 0 and ecs[i * len(presentVFAT2sSingle)] == 255):
                pass
            elif (ecs[(i + 1) * len(presentVFAT2sSingle)] - ecs[i * len(presentVFAT2sSingle)] != 1):
                print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, ecs[i * len(presentVFAT2sSingle)],
                                                                          ecs[(i+1) * len(presentVFAT2sSingle)])
                followingECS = False
                pass
            pass
        if (followingECS): print Passed
        else:
            print Failed
            testH = False
            pass
        pass
    writeRegister(glib,"%s.T1Controller.RESET"%(oh_basenode), 1)
    pass
else:
    print "   Skipping this test as the previous test did not succeed..."
    testH = False

print

####################################################

txtTitle("I. Testing the tracking data readout rate")
print "   Sending triggers at a given rate and looking at the maximum readout rate that can be achieved."

writeRegister(glib,"%s.GEB.Broadcast.Reset"%(oh_basenode), 0)
writeRegister(glib,"%s.GEB.Broadcast.Request.ContReg0"%(oh_basenode), 0)

writeRegister(glib,"%s.GEB.VFATS.VFAT%d"%(oh_basenode,presentVFAT2sSingle[0]), 55)
writeRegister(glib,"%s.CONTROL.VFAT.MASK"%(oh_basenode), ~(0x1 << presentVFAT2sSingle[0]))

f = open('out.log', 'w')

values = [
          100, 200, 300, 400, 500, 600, 700, 800, 900,
          1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
          10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
          100000, 125000, 150000, 175000, 200000
        ]

previous = 0

for i in values:
    isFull = False

    t1_mode     =  0
    t1_type     =  0
    t1_n        =  0
    t1_interval =  40000000 / i

    writeRegister(glib,"%s.T1Controller.RESET"%(oh_basenode), 1)
    flushTrackingFIFO(glib,options.gtx)
    sendL1A(glib,options.gtx,t1_interval,t1_n)

    if (RATE_WRITE):
        for j in range(0, 1000):
            depth = readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.DEPTH"%(options.gtx))
            if (depth > 0):
                if (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISEMPTY"%(options.gtx)) != 1):
                    data = readBlock(glib,"GLIB.TRK_DATA.OptoHybrid_%d.FIFO"%(options.gtx), 1*depth)
                    for d in data: f.write(str(d))
                    pass
                pass
            if (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISFULL"%(options.gtx)) == 1):
                isFull = True
                break
    else:
        for j in range(0, 1000):
            depth = readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.DEPTH"%(options.gtx))
            if (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISEMPTY"%(options.gtx)) != 1):
                readBlock(glib,"GLIB.TRK_DATA.OptoHybrid_%d.FIFO"%(options.gtx), 1*depth)
                pass
            if (readRegister(glib,"GLIB.TRK_DATA.OptoHybrid_%d.ISFULL"%(options.gtx)) == 1):
                isFull = True
                break

    if (isFull):
        print "   Maximum readout rate\t", str(previous), "Hz"
        break

    previous = i
    if options.debug:
        print "   Readout succeeded at \t", str(previous), "Hz"
        pass

    time.sleep(0.01)

f.close()

writeRegister(glib,"%s.T1Controller.RESET"%(oh_basenode), 1)
writeRegister(glib,"%s.GEB.VFATS.VFAT%d.ContReg0"%(oh_basenode,presentVFAT2sSingle[0]), 0)

testI = True

writeRegister(glib,"%s.CONTROL.VFAT.MASK"%(oh_basenode), 0)

print

####################################################

txtTitle("J. Testing the optical link error rate")

writeRegister(glib,"GLIB.COUNTERS.GTX%d.TRK_ERR.Reset"%(options.gtx), 1)
time.sleep(1)
glib_tk_error_reg = readRegister(glib,"GLIB.COUNTERS.GTX%d.TRK_ERR"%(options.gtx))

writeRegister(glib,"GLIB.COUNTERS.GTX%d.TRG_ERR.Reset"%(options.gtx), 1)
time.sleep(1)
glib_tr_error_reg = readRegister(glib,"GLIB.COUNTERS.GTX%d.TRG_ERR"%(options.gtx))

writeRegister(glib,"%s.COUNTERS.GTX.TRK_ERR"%(oh_basenode), 1)
time.sleep(1)
oh_tk_error_reg = readRegister(glib,"%s.COUNTERS.GTX.TRK_ERR"%(oh_basenode))

writeRegister(glib,"%s.COUNTERS.GTX.TRG_ERR"%(oh_basenode), 1)
time.sleep(1)
oh_tr_error_reg = readRegister(glib,"%s.COUNTERS.GTX.TRG_ERR"%(oh_basenode))

print "   GLIB tracking link error rate is of\t\t", str(glib_tk_error_reg), "Hz"
print "   GLIB trigger link error rate is of\t\t", str(glib_tr_error_reg), "Hz"
print "   OptoHybrid tracking link error rate is of\t", str(oh_tk_error_reg), "Hz"
print "   OptoHybrid trigger link error rate is of\t", str(oh_tr_error_reg), "Hz"

testJ = True

print

####################################################

txtTitle("K. Results")

print "   A.", (Passed if testA else Failed)
print "   B.", (Passed if testB else Failed)
print "   C.", (Passed if testC else Failed)
print "   D.", (Passed if testD else Failed)
print "   E.", (Passed if testE else Failed)
print "   F.", (Passed if testF else Failed)
print "   G.", (Passed if testG else Failed)
print "   H.", (Passed if testH else Failed)
print "   I.", (Passed if testI else Failed)
print "   J.", (Passed if testJ else Failed)

print
