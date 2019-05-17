#!/bin/env python

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Queries the DB for calibration info for all VFATs on given (shelf,slot,gtx)")
    parser.add_argument("--shelf",type=int,help="uTCA shelf number",default=2)
    parser.add_argument("-s","--slot",type=int,help="AMC slot in uTCA shelf",default=5)
    parser.add_argument("-g","--gtx",type=int,help="OH on AMC slot",default=2)
    parser.add_argument("-d","--debug",action="store_true",help="Prints additional information")
    parser.add_argument("--write2File",action="store_true",help="If Provided data will be written to appropriate calibration files")
    parser.add_argument("--write2CTP7",action="store_true",help="If Provided IREF data will be sent to the VFAT3 config files on the CTP7")
    args = parser.parse_args()

    from gempython.tools.vfat_user_functions_xhal import *
    
    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(args.shelf,args.slot)
    vfatBoard = HwVFAT(cardName,args.gtx)

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
        ohKey = (args.shelf, args.slot, args.gtx)
        
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
        pass

    # Write CFG_IREF to VFAT3 Config Files On CTP7?    
    if args.write2CTP7:
        import os
        from gempython.utils.wrappers import runCommand
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
            pass

        gemuserHome = "/mnt/persistent/gemuser/"
        # Copy Files
        copyFilesCmd = [
                'scp',
                filename_iref,
                'gemuser@{0}:{1}'.format(cardName,gemuserHome)
                ]
        runCommand(copyFilesCmd)

        # Update stored vfat config
        dacName="CFG_IREF"
        replaceStr = "/mnt/persistent/gemdaq/scripts/replace_parameter.sh -f {0}/NominalValues-{1}.txt {2} {3}".format(
                gemuserHome,
                dacName,
                dacName.replace("CFG_",""),
                args.gtx)
        transferCmd = [
                'ssh',
                'gemuser@{0}'.format(cardName),
                'sh -c "{0}"'.format(replaceStr)
                ]
        runCommand(transferCmd)
        pass

    print("goodbye")
