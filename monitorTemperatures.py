#!/bin/env python

if __name__ == '__main__':
    """
    Script to readout and record temperatures of the electronics
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="Reads and records temperature of electronics.  Will read in distinct time intervals until a keyboard interrupt (Ctrl+C) is sent")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("cardName", type=str, help="hostname of the AMC you are connecting too, e.g. 'eagle64'; if running on an AMC use 'local' instead", metavar="cardName")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")

    # Optional arguments
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            hep = "Print additional debugging information")
    parser.add_argument("--extRefADC", action="store_true", dest="extRefADC",
            help = "Use externally referenced ADC to monitor temperature values on VFAT3s")
    parser.add_argument("--extTempVFAT", action="store_true", dest="extTempVFAT",
            help = "Use external PT1000 temperature sensors on the VFAT3 hybrid instead of the temperature sensor inside the ASIC. Note only available in HV3b_V3 hybrids or later")
    parser.add_argument("-f","--filename", type=str, dest="filename", default="TemperatureData.root",
            help = "Specify output filename",metavar="filename")
    parser.add_argument("--timeInterval", type=int, dest="timeInterval", default=60,
            help ="Time interval, in seconds, to wait in between temperature reads",metavar="timeInterval")
    #parser.add_argument("--vfatmask", type="int", dest="vfatmask", default=0x0,
    #              help="24 bit number where a 1 in the N^th bit indicates to mask the N^th VFAT", metavar="vfatmask")
    args = parser.parse_args()

    import ROOT as r
    filename = options.filename
    myF = r.TFile(filename,'recreate')
    
    import subprocess,datetime,time
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print(startTime)
    Date = startTime
    
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    import os
    if amcBoard.fwVersion < 3:
        print("temperature monitoring of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)

    #mask = options.vfatmask

    # Configure DAC Monitoring
    tempSelect = 37
    if args.extTempVFAT:
        tempSelect = 38
    amcBoard.configureVFAT3DacMonitorMulti(tempSelect, args.ohMask)

    from sleep import time
    from ctypes import *
    adcDataMultiLinks = (c_uint32 * 24 * 12)()
    try:
        # place holder
        print("Reading and recording temperature data, press Ctrl+C to stop")
        while(True):
            # Read all ADCs
            rpcResp = amcBoard.readADCsMulti(adcDataMultiLinks, args.extRefADC, args.ohMask)

            if rpcResp != 0:
                raise Exception("RPC response was non-zero, reading all VFAT ADCs from OH's in ohMask = {0} failed".format(hex(args.ohMask)))

            # Wait 
            sleep(args.time)
            pass
    except KeyboardInterrupt:
        # Done
