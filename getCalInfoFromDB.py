#!/bin/env python

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Queries the DB for calibration info for all VFATs on given (shelf,slot,link)")
    parser.add_argument("shelf",type=int,help="uTCA shelf number")
    parser.add_argument("slot",type=int,help="AMC slot in uTCA shelf")
    parser.add_argument("link",type=int,help="OH on AMC slot")
    parser.add_argument("-d","--debug",action="store_true",help="Prints additional information")
    parser.add_argument("--write2File",action="store_true",help="If Provided data will be written to appropriate calibration files")
    parser.add_argument("--write2CTP7",action="store_true",help="If Provided IREF data will be sent to the VFAT3 config files on the CTP7")
    args = parser.parse_args()

    from gempython.tools.vfat_user_functions_xhal import *
    
    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName,args.link)

    mask = vfatBoard.parentOH.getVFATMask()
    chipIDs = vfatBoard.getAllChipIDs(mask)

    while(len(chipIDs) != 24):
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

    if args.write2File or args.write2CTP7:
        from gempython.gemplotting.utils.anautilities import getDataPath, getElogPath
        ohKey = (args.shelf, args.slot, args.link)
        
        from gempython.gemplotting.mapping.chamberInfo import chamber_config
        if ohKey in chamber_config:
            cName = chamber_config[ohKey]
            outDir="{0}/{1}".format(getDataPath(),chamber_config[ohKey])
        else:
            cName = "Detector"
            outDir=getElogPath()
            pass

    # Write calibration info to disk?
    if args.write2File:
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
        from gempython.utils.wrappers import runCommand
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

    # Write CFG_IREF to VFAT3 Config Files On CTP7?    
    if args.write2CTP7:
        import os
        filename_iref = "{0}/NominalValues-CFG_IREF.txt".format(outDir)
        if not os.path.isfile(filename_iref):
            filename_iref = "{0}/NominalValues-CFG_IREF.txt".format(outDir)
            print("Writing 'CFG_IREF' to file: {0}".format(filename_iref))
            dbInfo.to_csv(
                    path_or_buf=filename_iref,
                    sep="\t",
                    columns=['vfatN','iref'],
                    header=False,
                    index=False,
                    mode='w')
            from gempython.utils.wrappers import runCommand
            runCommand(["chmod", "g+rw", filename_iref])
            pass

        from gempython.utils.gemlogger import getGEMLogger
        import logging
        gemlogger = getGEMLogger(__name__)
        gemlogger.setLevel(logging.INFO)
    
        from gempython.vfatqc.utils.confUtils import updateVFAT3ConfFilesOnAMC
        updateVFAT3ConfFilesOnAMC(cardName,args.link,filename_iref,"CFG_IREF")
        pass

    print("goodbye")
