#!/usr/bin/env python

import sys, os, random, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/kernel")
from ipbus import *

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

glibIP = raw_input("> Enter the GLIB's IP address: ")
glib = GLIB(glibIP.strip())


GLIB_REG_TEST = raw_input("> Number of register tests to perform on the GLIB [100]: ")
OH_REG_TEST = raw_input("> Number of register tests to perform on the OptoHybrid [100]: ")
I2C_TEST = raw_input("> Number of I2C tests to perform on the VFAT2s [100]: ")
TK_RD_TEST = raw_input("> Number of tracking data packets to readout [100]: ")
RATE_WRITE = raw_input("> Write the data to disk when testing the rate [Y/n]: ")

GLIB_REG_TEST = 100 if GLIB_REG_TEST == "" else int(GLIB_REG_TEST)
OH_REG_TEST = 100 if OH_REG_TEST == "" else int(OH_REG_TEST)
I2C_TEST = 100 if I2C_TEST == "" else int(I2C_TEST)
TK_RD_TEST = 100 if TK_RD_TEST == "" else int(TK_RD_TEST)
RATE_WRITE = False if (RATE_WRITE == "N" or RATE_WRITE == "n") else True

print

####################################################

txtTitle("A. Testing the GLIB's presence")
print "   Trying to read the GLIB board ID... If this test fails, the script will stop."

if (glib.get("board_id") != 0): print Passed
else:
    print Failed
    sys.exit()

testA = True

print

####################################################

txtTitle("B. Testing the OH's presence")
print "   Trying to set the OptoHybrid registers... If this test fails, the script will stop."

glib.set("oh_clk_source", 1)
glib.set("oh_trigger_source", 1)
## added from pythonScript setup
glib.set("oh_sys_clk_src", 1)
glib.set("oh_sys_t1_src", 1)
glib.set("oh_sys_trigger_lim", 0)


if (glib.get("oh_trigger_source") == 1): print Passed
else:
    print Failed, "oh_trigger_source"
    sys.exit()
    pass

if (glib.get("oh_sys_t1_src") == 1): print Passed
else:
    print Failed, "oh_sys_t1_src"
    sys.exit()
    pass

testB = True

print

####################################################

txtTitle("C. Testing the GLIB registers")
print "   Performing single and FIFO reads on the GLIB counters and ensuring they increment."

countersSingle = []
countersFifo = []
countersTest = True

for i in range(0, GLIB_REG_TEST): countersSingle.append(glib.get("glib_cnt_stb_cnt"))
countersFifo = glib.fifoRead("glib_cnt_stb_cnt", GLIB_REG_TEST)

for i in range(1, GLIB_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
        countersTest = False
        pass
    if (countersFifo[i - 1] + 1 != countersFifo[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersFifo[i-1], countersFifo[i])
        countersTest = False
        pass

if (countersTest): print Passed
else: print Failed

testC = countersTest

print

####################################################

txtTitle("D. Testing the OH registers")
print "   Performing single and FIFO reads on the OptoHybrid counters and ensuring they increment."

countersSingle = []
countersFifo = []
countersTest = True

for i in range(0, OH_REG_TEST): countersSingle.append(glib.get("oh_cnt_wb_gtx_stb"))
countersFifo = glib.fifoRead("oh_cnt_wb_gtx_stb", OH_REG_TEST)

for i in range(1, OH_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
        countersTest = False
        pass
    if (countersFifo[i - 1] + 1 != countersFifo[i]):
        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersFifo[i-1], countersFifo[i])
        countersTest = False
        pass

if (countersTest): print Passed
else: print Failed

testD = countersTest

print

####################################################

txtTitle("E. Detecting the VFAT2s over I2C")
print "   Detecting VFAT2s on the GEM by reading out their chip ID."

presentVFAT2sSingle = []
presentVFAT2sFifo = []

glib.set("ei2c_reset", 0)
glib.get("vfat2_all_chipid0")
chipIDs = glib.fifoRead("ei2c_data", 24)

for i in range(0, 24):
    # missing VFAT shows 0x0003XX00 in I2C broadcast result
    #                    0x05XX0800
    # XX is slot number
    # so if ((result >> 16) & 0x3) == 0x3, chip is missing
    # or if ((result) & 0x30000)   == 0x30000, chip is missing
    if (((glib.get("vfat2_" + str(i) + "_chipid0") >> 24) & 0x5) != 0x5): presentVFAT2sSingle.append(i)
    if (((chipIDs[i] >> 16)  & 0x3) != 0x3): presentVFAT2sFifo.append(i)
    #if ((glib.get("vfat2_" + str(i) + "_chipid0")  & 0xff) != 0): presentVFAT2sSingle.append(i)
    #if ((chipIDs[i]& 0xff) != 0): presentVFAT2sFifo.append(i)

if (presentVFAT2sSingle == presentVFAT2sFifo): Passed
else: Failed

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
        glib.set("vfat2_" + str(i) + "_ctrl3", writeData)
        readData = glib.get("vfat2_" + str(i) + "_ctrl3") & 0xff
        if (readData == writeData): validOperations += 1
    glib.set("vfat2_" + str(i) + "_ctrl3", 0)
    if (validOperations == I2C_TEST):  print Passed, "#" + str(i)
    else:
        print Failed, "#%d received %d, expected %d"%(i, validOperations, I2C_TEST)
        testF = False

print

####################################################

txtTitle("G. Reading out tracking data")
print "   Sending triggers and testing if the Event Counter adds up."

glib.set("ei2c_reset", 0)
glib.set("vfat2_all_ctrl0", 0)

testG = True

for i in presentVFAT2sSingle:
    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 0)
    glib.set("t1_n", TK_RD_TEST)
    glib.set("t1_interval", 400)

    glib.set("vfat2_" + str(i) + "_ctrl0", 55)
    glib.set("oh_sys_vfat2_mask", ~(0x1 << i))
    glib.set("tk_data_rd", 0)

    nPackets = 0
    timeOut = 0
    ecs = []

    glib.set("t1_toggle", 1)

    while (glib.get("tk_data_cnt") != 7 * TK_RD_TEST):
        timeOut += 1
        if (timeOut == 10 * TK_RD_TEST): break
        pass
    while (glib.get("tk_data_empty") != 1):
        packets = glib.fifoRead("tk_data_rd", 7)
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)
        pass
    glib.set("vfat2_" + str(i) + "_ctrl0", 0)

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
        if (followingECS): print Passed, "#" + str(i)
        else:
            print Failed, "#%d received %d, expected %d, noncontinuous ECs"%(i, nPackets, TK_RD_TEST)
            raw_input("press enter to continue")
            testG = False

print

####################################################

txtTitle("H. Reading out tracking data")
print "   Turning on all VFAT2s and looking that all the Event Counters add up."

testH = True

if (testG):
    glib.set("ei2c_reset", 0)
    glib.set("vfat2_all_ctrl0", 55)

    mask = 0
    for i in presentVFAT2sSingle: mask |= (0x1 << i)
    glib.set("oh_sys_vfat2_mask", ~mask)

    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 2)
    glib.set("t1_n", 1)
    glib.set("t1_interval", 10)
    glib.set("t1_toggle", 1)

    glib.set("tk_data_rd", 1)

    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 0)
    glib.set("t1_n", TK_RD_TEST)
    glib.set("t1_interval", 300)
    glib.set("t1_toggle", 1)

    nPackets = 0
    timeOut = 0
    ecs = []

    while (glib.get("tk_data_cnt") != len(presentVFAT2sSingle) * TK_RD_TEST):
        timeOut += 1
        if (timeOut == 20 * TK_RD_TEST): break
        pass
    while (glib.get("tk_data_empty") != 1):
        packets = glib.fifoRead("tk_data_rd", 7)
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)
        pass
    glib.set("ei2c_reset", 0)
    glib.set("vfat2_all_ctrl0", 0)

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
    glib.set("t1_reset", 1)
    pass
else:
    print "   Skipping this test as the previous test did not succeed..."
    testH = False

print

####################################################

txtTitle("I. Testing the tracking data readout rate")
print "   Sending triggers at a given rate and looking at the maximum readout rate that can be achieved."

glib.set("ei2c_reset", 0)
glib.set("vfat2_all_ctrl0", 0)
glib.set("vfat2_" + str(presentVFAT2sSingle[0]) + "_ctrl0", 55)
glib.set("oh_sys_vfat2_mask", ~(0x1 << presentVFAT2sSingle[0]))

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

    glib.set("t1_reset", 1)
    glib.set("tk_data_rd", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 0)
    glib.set("t1_n", 0)
    glib.set("t1_interval", 40000000 / i)
    glib.set("t1_toggle", 1)

    if (RATE_WRITE):
        for j in range(0, 1000):
            depth = glib.get("tk_data_cnt")
            if (depth > 0):
                data = glib.fifoRead("tk_data_rd", depth)
                for d in data: f.write(str(d))
            if (glib.get("tk_data_full") == 1):
                isFull = True
                break
    else:
        for j in range(0, 1000):
            depth = glib.get("tk_data_cnt")
            glib.fifoRead("tk_data_rd", depth)
            if (glib.get("tk_data_full") == 1):
                isFull = True
                break

    if (isFull):
        print "   Maximum readout rate\t", str(previous), "Hz"
        break

    previous = i

    time.sleep(0.01)

f.close()

glib.set("t1_reset", 1)
glib.set("vfat2_" + str(presentVFAT2sSingle[0]) + "_ctrl0", 0)

testI = True

glib.set("oh_sys_vfat2_mask", 0)

print

####################################################

txtTitle("J. Testing the optical link error rate")

glib.set("glib_cnt_err_tk0", 1)
time.sleep(1)
glib_tk_error_reg = glib.get("glib_cnt_err_tk0")

glib.set("glib_cnt_err_tr0", 1)
time.sleep(1)
glib_tr_error_reg = glib.get("glib_cnt_err_tr0")

glib.set("oh_cnt_err_tk", 1)
time.sleep(1)
oh_tk_error_reg = glib.get("oh_cnt_err_tk")

glib.set("oh_cnt_err_tr", 1)
time.sleep(1)
oh_tr_error_reg = glib.get("oh_cnt_err_tr")

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
