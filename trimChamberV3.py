#!/bin/env python
"""
Script to set trimdac values on a V3 chamber
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

if __name__ == '__main__':
    from anautilities import getEmptyPerVFATList, rejectOutliersMADOneSided
    from array import array
    from fitting.fitScanData import ScanDataFitter
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import runCommand, envCheck
    from mapping.chamberInfo import chamber_config
    from qcoptions import parser
    
    import datetime, subprocess, sys
    import numpy as np
    
    #parser.add_option("--calFile", type="string", dest="calFile", default=None,
    #                  help="File specifying CAL_DAC to fC equations per VFAT",
    #                  metavar="calFile")
    parser.add_option("--calSF", type="int", dest = "calSF", default = 0,
                      help="Value of the CFG_CAL_FS register", metavar="calSF")
    parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                      help="Specify minimum channel number to scan", metavar="chMin")
    parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                      help="Specify maximum channel number to scan", metavar="chMax")
    parser.add_option("--dirPath", type="string", dest="dirPath", default=None,
                      help="Specify the path where the scan data should be stored", metavar="dirPath")
    parser.add_option("--latency", type="int", dest = "latency", default = 37,
                      help="Specify Latency", metavar="latency")
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    (options, args) = parser.parse_args()
    
    rangeFile = options.rangeFile
    ztrim = options.ztrim
    chMin = options.chMin
    chMax = options.chMax + 1
    print('trimming at z = %f'%ztrim)

    if options.dirPath == None: 
        envCheck('DATA_PATH')
        dataPath = os.getenv('DATA_PATH')
        startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
        print(startTime)
        dirPath = '%s/%s/trimming/z%f/%s'%(dataPath,chamber_config[options.gtx],ztrim,startTime)
    else: 
        dirPath = options.dirPath
        pass
    
    # Declare the hardware board and bias all vfats
    vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)
    if options.gtx in chamber_vfatDACSettings.keys():
        print("Configuring VFATs with chamber_vfatDACSettings dictionary values")
        for key in chamber_vfatDACSettings[options.gtx]:
            vfatBoard.paramsDefVals[key] = chamber_vfatDACSettings[options.gtx][key]
    vfatBoard.biasAllVFATs(options.vfatmask)
    print('biased VFATs')
    
    ###############
    # TRIMDAC = 0
    ###############
    # Configure for initial scan
    # Zero all channel registers for an initial starting point
    for chan in range(0,128):
        vfatBoard.setChannelRegisterAll(chan)
    
    # Scurve scan with trimdac set to 0
    filename_untrimmed = "%s/SCurveData_trimdac0.root"%dirPath
    cmd = [ "ultraScurve.py",
            "--shelf=%i"%(options.shelf),
            "-s%d"%(options.slot),
            "-g%d"%(options.gtx),
            "--chMin=%i"%(options.chMin),
            "--chMax=%i"%(options.chMax),
            "--latency=%i"%(options.latency),
            "--mspl=%i"%(options.mspl),
            "--nevts=%i"%(options.nevts),
            "--vfatmask=0x%x"%(options.vfatmask),
            "--filename=%s"%(filename_untrimmed)
            ]
    # Calibration File? No, do everything in DAQ units *first*
    #if options.calFile is not None:
    #    cmd.append("--calFile=%s"%(options.calFile) )
    # Debug Flag?
    if options.debug:
        cmd.append("--debug")
    # Voltage or current pulse?
    if options.voltageStepPulse:
        cmd.append("--voltageStepPulse")
    else:
        cmd.append("--calSF=%i"%(options.calSF) )
    runCommand(cmd)
    
    # Get the initial fit results
    fitResults_Untrimmed = fitScanData(filename_untrimmed, isVFAT3=True, calFileName=options.calFile)
    
    # Determine the position of interest (POI) for all s-curves
    # This is the position (X = scurve_mean - ztrim * scurve_sigma) on the curve
    array_avgScurvePOIPerVFAT = np.zeros(24)
    dict_scurvePOIPerChan = { vfat:np.zeros(128) for vfat in range(0,24) }
    dict_trimVal = { vfat:np.zeros(128) for vfat in range(0,24) }
    dict_vfatID = { vfat:0 for vfat in range(0,24) } # placeholder
    masks = ndict()
    chConfig = open("%s/chConfig.txt","w")
    chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')
    for vfat in range(0,24):
        # skip masked vfats
        if (options.vfatmask >> vfat) & 0x1: 
            continue
        
        # Determine scurve point of interest by channel
        for chan in range(chMin,chMax):
            # initial setpoint for masked channels
            if fitResults_Untrimmed[4][vfat][chan] < 0.1: 
                masks[vfat][chan] = True
                continue # do not consider channels w/empty s-curves
            else:
                masks[vfat][chan] = False
                pass
            
            # store the position
            dict_scurvePOIPerChan = int(round(fitResults_Untrimmed[0][vfat][chan] - ztrim * fitResults_Untrimmed[1][vfat][chan]))
            pass

        # Determine the position to trim to
        array_avgScurvePOIPerVFAT[vfat] = np.mean(
                rejectOutliersMADOneSided(
                    dict_scurvePOIPerChan[dict_scurvePOIPerChan > 0.],
                    rejectHighTail=False
                    )
                )
        array_avgScurvePOIPerVFAT[vfat] = int(round(array_avgScurvePOIPerVFAT[vfat]))
        dict_trimVal[vfat] = dict_scurvePOIPerChan[vfat] - array_avgScurvePOIPerVFAT[vfat] 

        # Tell the user what we are doing
        if options.debug:
            print("| vfatN | chan | scurvePOI | avgScurvePOI | trimVal | trimPol | Note |")
            print("| :---: | :--: | :-------: | :----------: | :-----: | :-----: | :--- |")
            for chan in range(chMin,chMax):
                chNote = ""
                if ( abs(dict_scurvePOIPerChan[vfat][chan]) > 0x7f):
                    chNote = "Needed TrimVal Exceeds Range"
                    pass
                print("| %i | %i | %i | %i | %i | %i | %s |"%(
                        vfat, 
                        chan,
                        dict_scurvePOIPerChan[vfat][chan],
                        array_avgScurvePOIPerVFAT[vfat],
                        dict_trimVal[vfat][chan],
                        int(dict_trimVal[vfat] >= 0),
                        chNote
                        )
                    )
                pass
            pass

        # Set the trim value
        for chan in range(chMin,chMax):
            # Check if it's possible to trim
            # If not, include the channel in the masks
            if ( abs(dict_trimVal[vfat][chan]) > 0x7f):
                masks[vfat][chan] = True

            # Determine trim polarity
            # if dict_trimVal[vfat] >= 0 scurve is above the average, need negative trim polarity
            # if dict_trimVal[vfat] <  0 scurve is below the average, need positive trim polarity
            trimPol = 0x0
            if (dict_trimVal[vfat][chan] >= 0):
                trimPol = 0x1
                pass

            # Store the trim config
            chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')
            chConfig.write('%i\t%i\t%i\t%i\t%i\t%i\n'%(
                vfat,
                dict_vfatID[vfat],
                chan,
                abs(dict_trimVal[vfat][chan]),
                trimPol,
                masks[vfat][chan]))

            # Set the trim value
            if options.debug:
                print("setting channel registers for vfat%i channel %i"%(vfat,chan))
                pass
            vfatBoard.setChannelRegister(
                    vfat,
                    chan,
                    mask=masks[vfat][chan],
                    trimARM=int(dict_trimVal[vfat][chan]),
                    trimARMPol=trimPol
                    )
            pass
        pass

    # close the config file
    chConfig.close()

    #####################
    # TRIMDAC = Trimmed #
    #####################
    # Scurve scan with trims set to the determined values
    filename_trimmed = "%s/SCurveData_trimmed.root"%dirPath
    cmd = [ "ultraScurve.py",
            "--shelf=%i"%(options.shelf),
            "-s%d"%(options.slot),
            "-g%d"%(options.gtx),
            "--chMin=%i"%(options.chMin),
            "--chMax=%i"%(options.chMax),
            "--latency=%i"%(options.latency),
            "--mspl=%i"%(options.mspl),
            "--nevts=%i"%(options.nevts),
            "--vfatmask=0x%x"%(options.vfatmask),
            "--filename=%s"%(filename_trimmed)
            ]
    # Calibration File? No, do everything in DAQ units *first*
    #if options.calFile is not None:
    #    cmd.append("--calFile=%s"%(options.calFile) )
    # Debug Flag?
    if options.debug:
        cmd.append("--debug")
    # Voltage or current pulse?
    if options.voltageStepPulse:
        cmd.append("--voltageStepPulse")
    else:
        cmd.append("--calSF=%i"%(options.calSF) )
    runCommand(cmd)

    print("trimming completed")
