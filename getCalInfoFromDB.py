#!/bin/env python

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Queries the DB for calibration info for all VFATs on given (shelf,slot,gtx)")
    parser.add_argument("--shelf",type=int,help="uTCA shelf number",default=2)
    parser.add_argument("-s","--slot",type=int,help="AMC slot in uTCA shelf",default=5)
    parser.add_argument("-g","--gtx",type=int,help="OH on AMC slot",default=2)
    args = parser.parse_args()

    from gempython.tools.vfat_user_functions_xhal import *
    
    vfatBoard = HwVFAT("gem-shelf%02d-amc%02d"%(args.shelf,args.slot),args.gtx)

    mask = vfatBoard.parentOH.getVFATMask()
    chipIDs = vfatBoard.getAllChipIDs(mask)

    while(len(chipIDs) != 24):
        chipIDs.append(0)

    for vfat,vfatID in enumerate(chipIDs):
        print vfat, vfatID

    from gempython.gemplotting.utils.dbutils import getVFAT3CalInfo
    dbInfo = getVFAT3CalInfo(chipIDs)

    import pandas as pd
    pd.set_option('display.max_columns', 500)
    dbInfo.info()
    print dbInfo

    print("goodbye")
