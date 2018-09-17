#!/bin/env python

if __name__ == '__main__':
    """
    Script to readout and record temperatures of the electronics

    If no filename option (e.g. -f, --filename) is specified a single read of all temperatures will be performed; then the program will exit.
    Otherwise the program will read temperatures every --timeInterval seconds and print the results to an output file.
    This will continue indefinitely until a keyboardInterrupt is issued.

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
            help = "Print additional debugging information")
    parser.add_argument("--extTempVFAT", action="store_true", dest="extTempVFAT",
            help = "Use external PT1000 temperature sensors on the VFAT3 hybrid instead of the temperature sensor inside the ASIC. Note only available in HV3b_V3 hybrids or later")
    parser.add_argument("-f","--filename", type=str, dest="filename", default=None,
            help = "Specify output filename",metavar="filename")
    parser.add_argument("--noOHs", action="store_true", dest="noOHs",
            help = "Do not print OH temperatures to terminal; they are still read and stored in the output file if provided")
    parser.add_argument("--noVFATs", action="store_true", dest="noVFATs",
            help = "Do not print VFAT temperatures to terminal; they are still read and stored in the output file if provided")
    parser.add_argument("-t","--timeInterval", type=int, dest="timeInterval", default=60,
            help ="Time interval, in seconds, to wait in between temperature reads",metavar="timeInterval")
    args = parser.parse_args()

    if args.filename is not None:
        import ROOT as r
        filename = args.filename
        outF = r.TFile(filename,'recreate')

        from gempython.vfatqc.treeStructure import gemTemepratureOHTree, gemTemepratureVFATTree
        gemTempDataOH = gemTemepratureOHTree()
        gemTempDataVFAT = gemTemepratureVFATTree()

    from gempython.tools.amc_user_functions_xhal import *
    amcBoard = HwAMC(args.cardName, args.debug)
    print('opened connection')

    import os
    if amcBoard.fwVersion < 3:
        print("temperature monitoring of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)

    print("Getting VFAT Mask for All Links")
    ohVFATMaskArray = amcBoard.getMultiLinkVFATMask(args.ohMask)
    print("Getting CHIP IDs of all VFATs")
    from gempython.utils.nesteddict import nesteddict as ndict
    vfatIDvals = ndict()
    for ohN in range(0,12):
        if( not ((args.ohMask >> ohN) & 0x1)):
            continue
        vfatBoard = HwVFAT(args.cardName, ohN, args.debug)
        vfatIDvals[ohN] = vfatBoard.getAllChipIDs(mask)

    # Configure DAC Monitoring
    print("configuring VFAT ADCs for temperature monitoring")
    tempSelect = 37
    if args.extTempVFAT:
        tempSelect = 38
    amcBoard.configureVFAT3DacMonitorMulti(tempSelect, args.ohMask)
    print("VFAT ADCs have been configured for temperature monitoring")

    # Remove this once a register for monitoring FPGA Core Temp Exists
    print("Configuring SCA JTAG Registers")
    origSCAMonOffVal = amcBoard.readRegister("GEM_AMC.SLOW_CONTROL.SCA.ADC_MONITORING.MONITORING_OFF")
    from reg_utils.reg_interface.common.jtag import disableJtag, enableJtag, initJtagRegAddrs, jtagCommand
    initJtagRegAddrs()
    enableJtag(args.ohMask,2)

    # This must come after enableJtag() otherwise Monitoring will be disabled
    print("Enabling SCA Monitoring")
    amcBoard.scaMonitorToggle(~args.ohMask & 0xFF)
    print("SCA Monitoring Enabled, set to {0}".format(str(hex(~args.ohMask & 0xFF)).strip('L')))

    from time import sleep
    from ctypes import *
    adcDataIntRefMultiLinks = (c_uint32 * (24 * 12))()
    adcDataExtRefMultiLinks = (c_uint32 * (24 * 12))()
    try:
        # place holder
        print("Reading and recording temperature data, press Ctrl+C to stop")

        from reg_utils.reg_interface.common.sca_utils import getOHlist
        from reg_utils.reg_interface.common.virtex6 import Virtex6Instructions
        while(True):
            # Read all ADCs
            print("Reading Internally Referenced ADC data")
            rpcResp = amcBoard.readADCsMultiLink(adcDataIntRefMultiLinks, False, args.ohMask, args.debug)
            print("Internally Referenced ADC Data was read")

            if rpcResp != 0:
                raise Exception("RPC response was non-zero, reading all VFAT ADCs from OH's in ohMask = {0} failed".format(hex(args.ohMask)))

            print("Reading Externally Referenced ADC data")
            rpcResp = amcBoard.readADCsMultiLink(adcDataExtRefMultiLinks, True, args.ohMask, args.debug)
            print("Externally Referenced ADC Data was read")

            if rpcResp != 0:
                raise Exception("RPC response was non-zero, reading all VFAT ADCs from OH's in ohMask = {0} failed".format(hex(args.ohMask)))

            print("Reading SCA Temperatures")
            scaMonData = amcBoard.scaMonitorMultiLink(ohMask=args.ohMask)
            print("SCA Temperatures Have Been Read")

            print("Reading FPGA Core Temperature")
            ohList = getOHlist(args.ohMask)
            jtagCommand(True, Virtex6Instructions.SYSMON, 10, 0x04000000, 32, False)
            sleep(1)
            adc1 = jtagCommand(False, None, 0, 0x04010000, 32, ohList)
            #adc1 = jtagCommand(True, None, 0, 0x04010000, 32, ohList)
            sleep(1)
            jtagCommand(True, Virtex6Instructions.BYPASS, 10, None, 0, False)
            sleep(1)

            if not args.noVFATs:
                print("VFAT Raw Temperature Data in ADC Counts\n")
                print("| ohN | vfatN | vfatID | Int ADC Val | Ext ADC Val |")
                print("| :-: | :---: | :----: | :---------: | :---------: |")
                for ohN in range(0,12):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue
                    for vfat in range(0,24):
                        idx = ohN * 24 + vfat
                        print("| {0} | {1} | {2} | {3} | {4} |".format(
                            ohN,
                            vfat,
                            vfatIDvals[ohN][vfat],
                            adcDataIntRefMultiLinks[idx],
                            adcDataExtRefMultiLinks[idx]))
                        pass
                    pass

            if not args.noOHs:
                print("Optohybrid Temperature Data, in ADC Counts unless noted otherwise\n")
                headingTxt = "| ohN | FPGA Core (deg C) | SCA Temp |"
                headingLine= "| :-: | :---------------: | :------: |"
                for boardTemp in range(1,10):
                    headingTxt += " Board Temp {0} |".format(boardTemp)
                    headingLine+= " :----------: |"
                print(headingTxt)
                print(headingLine)
                for ohN in range(0,12):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue
                    row = "| {0} | {1} | {2} |".format(
                            ohN,
                            #scaMonData[ohN].ohFPGACoreTemp,
                            ((adc1[ohN] >> 6) & 0x3FF) * 503.975 / 1024.0-273.15, # Remove once dedicated register exists
                            scaMonData[ohN].scaTemp)
                    for boardTemp in range(1,10):
                        row += " {0} |".format(scaMonData[ohN].ohBoardTemp[boardTemp-1])
                    print(row)

            if(args.filename is None):
                break
            else:
                currentTime = int(time.time())
                for ohN in range(0,12):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue
                    for vfat in range(0,24):
                        idx = ohN * 24 + vfat
                        gemTempDataVFAT.fill(
                                adcTempIntRef = adcDataIntRefMultiLinks[idx],
                                adcTempExtRef = adcDataExtRefMultiLinks[idx]
                                link = ohN,
                                vfatID = vfatIDvals[ohN][vfat],
                                vfatN = vfat,
                                utime = currentTime
                                )
                        pass
                    pass

                for ohN in range(0,12):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue
                    gemTempDataOH.fill(
                            boardTemp1 = scaMonData[ohN].ohBoardTemp[0],
                            boardTemp2 = scaMonData[ohN].ohBoardTemp[1],
                            boardTemp3 = scaMonData[ohN].ohBoardTemp[2],
                            boardTemp4 = scaMonData[ohN].ohBoardTemp[3],
                            boardTemp5 = scaMonData[ohN].ohBoardTemp[4],
                            boardTemp6 = scaMonData[ohN].ohBoardTemp[5],
                            boardTemp7 = scaMonData[ohN].ohBoardTemp[6],
                            boardTemp8 = scaMonData[ohN].ohBoardTemp[7],
                            boardTemp9 = scaMonData[ohN].ohBoardTemp[8],
                            #fpgaCoreTemp = scaMonData[ohN].ohFPGACoreTemp
                            fpgaCoreTemp = ((adc1[ohN] >> 6) & 0x3FF) * 503.975 / 1024.0-273.15, # Remove once dedicated register exists
                            link = ohN,
                            scaTemp = scaMonData[ohN].scaTemp
                            utime = currentTime
                            )
                    pass

                gemTempDataOH.AutoSave("SaveSelf")
                gemTempDataVFAT.AutoSave("SaveSelf")

            # Wait 
            sleep(args.timeInterval)
            pass
    except KeyboardInterrupt:
        print("Finished Monitoring Temperatures")
        pass
    except Exception as e:
        if args.filename is not None:
            gemTempDataOH.AutoSave("SaveSelf")
            gemTempDataVFAT.AutoSave("SaveSelf")
        print "An exception occurred", e
    finally:
        if args.filename is not None:
            outF.cd()
            gemTempDataOH.Write()
            gemTempDataVFAT.Write()
            outF.Close()

    print("Reverting SCA Monitoring To Original Value")
    amcBoard.scaMonitorToggle(origSCAMonOffVal)
    print("SCA Monitoring Reverted to {0}".format(str(hex(origSCAMonOffVal)).strip('L')))

    disableJtag()

    # Done
    print "Done"
