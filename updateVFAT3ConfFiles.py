#!/bin/env python

from gempython.utils.gemlogger import getGEMLogger,printRed,printYellow
import logging

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Queries the DB for calibration info for all VFATs on given (shelf,slot,gtx)")
    parser.add_argument("shelf",type=int,help="uTCA shelf number")
    parser.add_argument("slot",type=int,help="AMC slot in uTCA shelf")
    parser.add_argument("link",type=int,help="OH on AMC slot")
    parser.add_argument("-d","--debug",action="store_true",help="Prints additional information")
    parser.add_argument("--dacSelect",type=int,help="DAC selection, see VFAT3 Manual 'Table 25: GBL CFG CTR 4 : Monitoring settings', if not provided all DAC's will be sent",default=None) 
    parser.add_argument("--scandate",type=str,help="DAC Scan scandate to use",default="current")

    args = parser.parse_args()

    # Set logging level to INFO if debug requested
    if args.debug:
        gemlogger = getGEMLogger(__name__)
        gemlogger.setLevel(logging.INFO)

    # Check to make sure (shelf,slot,key) exists in chamber_config
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    ohKey = (args.shelf,args.slot,args.link)
    import os
    if ohKey not in chamber_config:
        printRed("I did not find (shelf,slot,link) = {0} in the chamber_config dictionary.\nExiting".format(ohKey))
        exit(os.EX_USAGE)
    cName = chamber_config[ohKey]

    # Determine Card Name
    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(args.shelf,args.slot)

    from gempython.tools.hw_constants import maxVfat3DACSize
    from gempython.gemplotting.utils.anautilities import getDataPath
    from gempython.vfatqc.utils.confUtils import updateVFAT3ConfFilesOnAMC
    dataPath = getDataPath()
    if args.dacSelect is None:
        # Send IREF values
        filename_iref = "{0}/{1}/NominalValues-CFG_IREF.txt".format(dataPath,cName)
        if os.path.isfile(filename_iref):
            print("Sending CFG_IREF Information to CTP7")
            updateVFAT3ConfFilesOnAMC(cardName,args.link,filename_iref,"CFG_IREF")
            pass

        # Send values from DAC Scan
        for dacSelect,dacInfo in maxVfat3DACSize.iteritems():
            dacName = dacInfo[1]
            
            # Skip irrelevant DAC's
            if dacName == "CFG_CAL_DAC":
                continue
            elif dacName == "CFG_THR_ARM_DAC":
                continue
            elif dacName == "CFG_THR_ZCC_DAC":
                continue
            elif dacName == "CFG_VREF_ADC":
                continue

            # Check if File Exists
            filename = "{0}/{1}/dacScans/{2}/NominalValues-{3}.txt".format(
                    dataPath,
                    cName,
                    args.scandate,
                    dacName)
            if not os.path.isfile(filename):
                printYellow("Nominal Values File {0} does not exist or is not readable, skipping DAC {1}".format(filename,dacName))
                continue

            print("Sending {0} Information to CTP7".format(dacName))
            updateVFAT3ConfFilesOnAMC(cardName,args.link,filename,dacName)
            pass
    else:
        if args.dacSelect not in maxVfat3DACSize.keys():
            printRed("Input DAC selection {0} not understood".format(args.dacSelect))
            printRed("possible options include:")
            from gempython.vfatqc.utils.qcutilities import printDACOptions
            printDACOptions()
            exit(os.EX_USAGE)
            pass

        # Check if File Exists
        dacName = maxVfat3DACSize[args.dacSelect][1]
        filename = "{0}/{1}/dacScans/{2}/NominalValues-{3}.txt".format(
                dataPath,
                cName,
                args.scandate,
                dacName)
        if not os.path.isfile(filename):
            printRed("Nominal Values File {0} does not exist or is not readable.\nExiting!".format(filename))
            exit(os.EX_USAGE)

        print("Sending {0} Information to CTP7".format(dacName))
        updateVFAT3ConfFilesOnAMC(cardName,args.link,filename,dacName)
        pass

    print("DAC Info Transferred Successfully.\nGoodbye")
