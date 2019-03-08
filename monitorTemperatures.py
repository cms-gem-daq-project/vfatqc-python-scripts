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
    parser = argparse.ArgumentParser(description="Reads and records temperature of electronics.  If the --filename argument is not specified a single read will be performed then this script will exit.  If the --filename argument is provided this script will read in user specified time intervals until a keyboard interrupt (Ctrl+C) is sent")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_option("shelf", type=int, help="uTCA shelf to access")
    parser.add_option("slot", type=int,help="slot in the uTCA of the AMC you are connceting too")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")

    # Optional arguments
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            help = "Print additional debugging information")
    parser.add_argument("--extTempVFAT", action="store_true", dest="extTempVFAT",
            help = "Use external PT100 temperature sensors on the VFAT3 hybrid instead of the temperature sensor inside the ASIC. Note only available in HV3b_V3 hybrids or later")
    parser.add_argument("-f","--filename", type=str, dest="filename", default=None,
            help = "Specify output filename to store data in.  Will cause successive reads to be performed",metavar="filename")
    parser.add_argument("--noOHs", action="store_true", dest="noOHs",
            help = "Do not print OH temperatures to terminal; if --filename is provided OH temperatures are still read and stored in the output file")
    parser.add_argument("--noVFATs", action="store_true", dest="noVFATs",
            help = "Do not print VFAT temperatures to terminal; if --filename isp provided VFAT temperatures are still read and stored in the output file")
    parser.add_argument("-t","--timeInterval", type=int, dest="timeInterval", default=60,
            help ="Time interval, in seconds, to wait in between temperature reads",metavar="timeInterval")
    args = parser.parse_args()

    if args.filename is not None:
        import ROOT as r
        filename = args.filename
        outF = r.TFile(filename,'recreate')

        from gempython.vfatqc.utils.treeStructure import gemTemepratureOHTree, gemTemepratureVFATTree
        gemTempDataOH = gemTemepratureOHTree()
        gemTempDataVFAT = gemTemepratureVFATTree()

    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName, 0, args.debug) # Set a dummy link for now
    amcBoard = vfatBoard.parentOH.parentAMC
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
        vfatBoard.parentOH.link = ohN
        vfatIDvals[ohN] = vfatBoard.getAllChipIDs(ohVFATMaskArray[ohN])

    # Configure DAC Monitoring
    print("configuring VFAT ADCs for temperature monitoring")
    tempSelect = 37
    if args.extTempVFAT:
        tempSelect = 38
    amcBoard.configureVFAT3DacMonitorMulti(tempSelect, args.ohMask)
    print("VFAT ADCs have been configured for temperature monitoring")

    print("Enabling SCA Monitoring")
    origSCAMonOffVal = amcBoard.readRegister("GEM_AMC.SLOW_CONTROL.SCA.ADC_MONITORING.MONITORING_OFF")
    amcBoard.scaMonitorToggle(~args.ohMask & 0xFF)
    print("SCA Monitoring Enabled, set to {0}".format(str(hex(~args.ohMask & 0xFF)).strip('L')))

    from time import sleep, time
    from ctypes import *
    adcDataIntRefMultiLinks = (c_uint32 * (24 * 12))()
    adcDataExtRefMultiLinks = (c_uint32 * (24 * 12))()
    try:
        print("Reading and recording temperature data, press Ctrl+C to stop")

        while(True):
            # Read all ADCs
            print("Reading Internally Referenced ADC data")
            rpcResp = amcBoard.readADCsMultiLink(adcDataIntRefMultiLinks, False, args.ohMask, args.debug)

            if rpcResp != 0:
                raise Exception("RPC response was non-zero, reading all VFAT ADCs from OH's in ohMask = {0} failed".format(hex(args.ohMask)))

            print("Reading Externally Referenced ADC data")
            rpcResp = amcBoard.readADCsMultiLink(adcDataExtRefMultiLinks, True, args.ohMask, args.debug)

            if rpcResp != 0:
                raise Exception("RPC response was non-zero, reading all VFAT ADCs from OH's in ohMask = {0} failed".format(hex(args.ohMask)))

            print("Reading SCA Temperatures")
            scaMonData = amcBoard.scaMonitorMultiLink(ohMask=args.ohMask)

            print("Reading FPGA Core Temperature")
            sysmonData = amcBoard.sysmonMonitorMultiLink(ohMask=args.ohMask)
            print("Succeeded in reading FPGA Core Temperature")

            if not args.noVFATs:
                print("\nVFAT Raw Temperature Data in ADC Counts\n")
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
                            str(hex(vfatIDvals[ohN][vfat])).strip('L'),
                            adcDataIntRefMultiLinks[idx],
                            adcDataExtRefMultiLinks[idx]))
                        pass
                    pass
                print("")

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
                            ((sysmonData[ohN].fpgaCoreTemp * 503.975) / 1024.0 - 273.15),
                            scaMonData[ohN].scaTemp)
                    for boardTemp in range(1,10):
                        row += " {0} |".format(scaMonData[ohN].ohBoardTemp[boardTemp-1])
                    print(row)
                print("")

            if(args.filename is None):
                break
            else:
                currentTime = int(time())
                for ohN in range(0,12):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue
                    for vfat in range(0,24):
                        idx = ohN * 24 + vfat

                        gemTempDataVFAT.fill(
                                adcTempIntRef = adcDataIntRefMultiLinks[idx],
                                adcTempExtRef = adcDataExtRefMultiLinks[idx],
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
                            ohBoardTemp1 = scaMonData[ohN].ohBoardTemp[0],
                            ohBoardTemp2 = scaMonData[ohN].ohBoardTemp[1],
                            ohBoardTemp3 = scaMonData[ohN].ohBoardTemp[2],
                            ohBoardTemp4 = scaMonData[ohN].ohBoardTemp[3],
                            ohBoardTemp5 = scaMonData[ohN].ohBoardTemp[4],
                            ohBoardTemp6 = scaMonData[ohN].ohBoardTemp[5],
                            ohBoardTemp7 = scaMonData[ohN].ohBoardTemp[6],
                            ohBoardTemp8 = scaMonData[ohN].ohBoardTemp[7],
                            ohBoardTemp9 = scaMonData[ohN].ohBoardTemp[8],
                            fpgaCoreTemp = ((sysmonData[ohN].fpgaCoreTemp * 503.975) / 1024.0 - 273.15),
                            link = ohN,
                            scaTemp = scaMonData[ohN].scaTemp,
                            utime = currentTime
                            )
                    pass

                gemTempDataOH.autoSave("SaveSelf")
                gemTempDataVFAT.autoSave("SaveSelf")

            # Wait 
            sleep(args.timeInterval)
            pass
    except KeyboardInterrupt:
        print("Finished Monitoring Temperatures")
        pass
    except Exception as e:
        if args.filename is not None:
            gemTempDataOH.autoSave("SaveSelf")
            gemTempDataVFAT.autoSave("SaveSelf")
        print "An exception occurred", e
    finally:
        if args.filename is not None:
            outF.cd()
            gemTempDataOH.write()
            gemTempDataVFAT.write()
            outF.Close()

    print("Reverting SCA Monitoring To Original Value")
    amcBoard.scaMonitorToggle(origSCAMonOffVal)
    print("SCA Monitoring Reverted to {0}".format(str(hex(origSCAMonOffVal)).strip('L')))

    #disableJtag()

    # Done
    print "Done"
