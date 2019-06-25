#!/bin/env python

if __name__ == '__main__':
    import argparse
    from gempython.tools.hw_constants import gemVariants
    parser = argparse.ArgumentParser(description="Queries the DB for calibration info for all VFATs on given (shelf,slot,link)")
    parser.add_argument("shelf",type=int,help="uTCA shelf number")
    parser.add_argument("slot",type=int,help="AMC slot in uTCA shelf")
    parser.add_argument("link",type=int,help="OH on AMC slot")
    parser.add_argument("-d","--debug",action="store_true",help="Prints additional information")
    parser.add_argument("--write2File",action="store_true",help="If Provided data will be written to appropriate calibration files")
    parser.add_argument("--write2CTP7",action="store_true",help="If Provided IREF data will be sent to the VFAT3 config files on the CTP7")
    parser.add_argument("--gemType",type=str,help="String that defines the GEM variant, available from the list: {0}".format(gemVariants.keys()),default="ge11")
    parser.add_argument("--detType",type=str,help="Detector type within gemType. If gemType is 'ge11' then this should be from list {0}; if gemType is 'ge21' then this should be from list {1}; and if type is 'me0' then this should be from the list {2}".format(gemVariants['ge11'],gemVariants['ge21'],gemVariants['me0']),default="short")
    args = parser.parse_args()

    # Update the files on the DAQ machine whenever an update on the CTP7 is requested
    # This avoids sending stale data on the CTP7 if --write2File is not set
    if args.write2CTP7:
        args.write2File = True

    from gempython.tools.vfat_user_functions_xhal import *

    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName, link=args.link, gemType=args.gemType, detType=args.detType)

    mask = vfatBoard.parentOH.getVFATMask()
    chipIDs = vfatBoard.getAllChipIDs(mask)

    while(len(chipIDs) < vfatBoard.parentOH.nVFATs):
        chipIDs.append(0)

    if args.debug:
        for vfat,vfatID in enumerate(chipIDs):
            print(vfat, vfatID)

    from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
    dbInfo = getVFAT3CalInfo(chipIDs)

    import pandas as pd
    pd.set_option('display.max_columns', 500)
    dbInfo.info()
    print(dbInfo)

    # Write calibration info to disk?
    if args.write2File:
        from gempython.gemplotting.utils.anautilities import getDataPath, getElogPath
        from gempython.gemplotting.mapping.chamberInfo import chamber_config
        from gempython.utils.wrappers import runCommand

        ohKey = (args.shelf, args.slot, args.link)

        if ohKey in chamber_config:
            cName = chamber_config[ohKey]
            outDir="{0}/{1}".format(getDataPath(),chamber_config[ohKey])
        else:
            cName = "Detector"
            outDir=getElogPath()
            pass

        # Write VREF_ADC Info
        filename_vref_adc = "{0}/NominalValues-CFG_VREF_ADC.txt".format(outDir)
        print("Writing 'CFG_VREF_ADC' to file: {0}".format(filename_vref_adc))
        dbInfo.to_csv(
                path_or_buf=filename_vref_adc,
                sep="\t",
                columns=['vfatN','vref_adc'],
                header=False,
                index=False,
                mode='w')
        runCommand(["chmod", "g+rw", filename_vref_adc])

        # Write IREF Info
        filename_iref = "{0}/NominalValues-CFG_IREF.txt".format(outDir)
        print("Writing 'CFG_IREF' to file: {0}".format(filename_iref))
        dbInfo.to_csv(
                path_or_buf=filename_iref,
                sep="\t",
                columns=['vfatN','iref'],
                header=False,
                index=False,
                mode='w')
        runCommand(["chmod", "g+rw", filename_iref])

        # Write ADC0 Info
        filename_adc0 = "{0}/calFile_ADC0_{1}.txt".format(outDir,cName)
        print("Writing 'ADC0' Calibration file: {0}".format(filename_adc0))
        file_adc0 = open(filename_adc0,"w")
        file_adc0.write("vfatN/I:slope/F:intercept/F\n")
        dbInfo.to_csv(
                path_or_buf=file_adc0,
                sep="\t",
                columns=['vfatN','adc0m','adc0b'],
                header=False,
                index=False,
                mode='a')
        runCommand(["chmod", "g+rw", filename_adc0])

        # Write CAL_DAC Info
        filename_caldac = "{0}/calFile_calDac_{1}.txt".format(outDir,cName)
        print("Writing 'CAL_DAC' Calibration file: {0}".format(filename_caldac))
        file_caldac = open(filename_caldac,"w")
        file_caldac.write("vfatN/I:slope/F:intercept/F\n")
        dbInfo.to_csv(
                path_or_buf=file_caldac,
                sep="\t",
                columns=['vfatN','cal_dacm','cal_dacb'],
                header=False,
                index=False,
                mode='a')
        runCommand(["chmod", "g+rw", filename_caldac])
        pass

    # Write CFG_VREF_ADC and CFG_IREF to VFAT3 Config Files On CTP7?
    if args.write2CTP7:
        from gempython.utils.gemlogger import getGEMLogger
        import logging
        gemlogger = getGEMLogger(__name__)
        gemlogger.setLevel(logging.INFO)

        from gempython.vfatqc.utils.confUtils import updateVFAT3ConfFilesOnAMC
        updateVFAT3ConfFilesOnAMC(cardName,args.link,filename_iref,"CFG_IREF")
        updateVFAT3ConfFilesOnAMC(cardName,args.link,filename_vref_adc,"CFG_VREF_ADC")
        pass

    print("goodbye")
