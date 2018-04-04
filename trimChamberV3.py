#!/bin/env python
"""
Script to set trimdac values on a V3 chamber
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

if __name__ == '__main__':
    from anautilities import getEmptyPerVFATList, rejectOutliersMADOneSided
    from array import array
    from ctypes import *
    #from fitting.fitScanData import ScanDataFitter
    from fitting.fitScanData import fitScanData
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import runCommand, envCheck
    from mapping.chamberInfo import chamber_config, chamber_vfatDACSettings
    from qcoptions import parser
    
    import datetime, subprocess, sys
    import numpy as np
    
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
    parser.add_option("--printSummary", action="store_true", dest="printSummary",
                      help="Prints a summary table describing the results before and after trimming",
                      metavar="printSummary")
    parser.add_option("--resume", action="store_true",dest="resume",
                      help="Tries to resume a previous scurve scan by searching the --dirPath directory for the SCurveData_trimdac0.root file, if this scan completed successfully resuming will be attempted", 
                      metavar="resume")
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    (options, args) = parser.parse_args()
    
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
   
    if not options.resume:
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
        print("zero'ing all channel registers")
        rpcResp = vfatBoard.setAllChannelRegisters(vfatMask=options.vfatmask)
        
        if rpcResp != 0:
            raise Exception("RPC response was non-zero, zero'ing all channel registers failed")

        # Scurve scan with trimdac set to 0
        print("taking an initial s-curve")
        filename_untrimmed = "%s/SCurveData_trimdac0.root"%dirPath
        cmd = [ "ultraScurve.py",
                "--shelf=%i"%(options.shelf),
                "-s%d"%(options.slot),
                "-g%d"%(options.gtx),
                "--chMin=%i"%(options.chMin),
                "--chMax=%i"%(options.chMax),
                "--latency=%i"%(options.latency),
                "--mspl=%i"%(options.MSPL),
                "--nevts=%i"%(options.nevts),
                "--vfatmask=0x%x"%(options.vfatmask),
                "--filename=%s"%(filename_untrimmed)
                ]
        # Debug Flag?
        #if options.debug:
        #    cmd.append("--debug")
        # Voltage or current pulse?
        if options.voltageStepPulse:
            cmd.append("--voltageStepPulse")
        else:
            cmd.append("--calSF=%i"%(options.calSF) )
        runCommand(cmd)
        print("initial scurve finished")
    else:
        vfatBoard = HwVFAT(options.slot, options.gtx, options.shelf, options.debug)
        filename_untrimmed = "%s/SCurveData_trimdac0.root"%dirPath

    # Get the initial fit results
    print("fitting results, this may take some time")
    fitResults_Untrimmed = fitScanData(treeFileName=filename_untrimmed, isVFAT3=True)
    print("fitting has completed")

    # Create the output file which will store the channel configurations
    chConfig = open("%s/chConfig.txt"%dirPath,"w")
    chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')
    
    # Make the cArrays
    cArray_Masks = (c_uint32 * 3072)()
    cArray_trimVal = (c_uint32 * 3072)()
    cArray_trimPol = (c_uint32 * 3072)()

    # Determine the position of interest (POI) for all s-curves
    # This is the position (X = scurve_mean - ztrim * scurve_sigma) on the curve
    array_avgScurvePOIPerVFAT = np.zeros(24)
    dict_scurvePOIPerChan = { vfat:np.zeros(128) for vfat in range(0,24) }
    dict_trimVal = { vfat:np.zeros(128) for vfat in range(0,24) }
    dict_vfatID = { vfat:0 for vfat in range(0,24) } # placeholder
    print("Analyzing the fit data to determine the trim values")
    for vfat in range(0,24):
        # skip masked vfats
        if (options.vfatmask >> vfat) & 0x1: 
            continue
        
        # Determine scurve point of interest by channel
        for chan in range(chMin,chMax):
            idx = 128*vfat + chan

            # initial setpoint for masked channels
            if fitResults_Untrimmed[4][vfat][chan] < 0.1: 
                cArray_Masks[idx] = 1 # True
                continue # do not consider channels w/empty s-curves
            else:
                cArray_Masks[idx] = 0 # False
                pass
            
            # store the position and mask negative scurve POI's
            dict_scurvePOIPerChan[vfat][chan] = int(round(fitResults_Untrimmed[0][vfat][chan] - ztrim * fitResults_Untrimmed[1][vfat][chan]))
            if (dict_scurvePOIPerChan[vfat][chan] < 0):
                cArray_Masks[idx] = 1 # True
                pass
            pass

        # Determine the position to trim to
        dict_scurvePOIPerChan_OnlyNonzero = dict_scurvePOIPerChan[vfat][dict_scurvePOIPerChan[vfat] > 0.]
        if len(dict_scurvePOIPerChan_OnlyNonzero) > 0:
            array_avgScurvePOIPerVFAT[vfat] = np.mean(
                    rejectOutliersMADOneSided(
                        dict_scurvePOIPerChan_OnlyNonzero,
                        rejectHighTail=False
                        )
                    )
            array_avgScurvePOIPerVFAT[vfat] = int(round(array_avgScurvePOIPerVFAT[vfat]))
            dict_trimVal[vfat] = dict_scurvePOIPerChan[vfat] - array_avgScurvePOIPerVFAT[vfat] 
        else:
            array_avgScurvePOIPerVFAT[vfat] = -1
            dict_trimVal[vfat] = dict_scurvePOIPerChan[vfat] * 0 # Set all trim's to zero
            pass

        # Tell the user what we are doing
        if options.debug:
            print("| vfatN | chan | scurvePOI | avgScurvePOI | trimVal | trimPol | Note |")
            print("| :---: | :--: | :-------: | :----------: | :-----: | :-----: | :--- |")
            for chan in range(chMin,chMax):
                chNote = " - "
                if ( abs(dict_trimVal[vfat][chan]) > 0x7f):
                    chNote = "Needed TrimVal Exceeds Range"
                    pass
                print("| %i | %i | %i | %i | %i | %i | %s |"%(
                        vfat, 
                        chan,
                        dict_scurvePOIPerChan[vfat][chan],
                        array_avgScurvePOIPerVFAT[vfat],
                        abs(dict_trimVal[vfat][chan]),
                        int(dict_trimVal[vfat][chan] >= 0),
                        chNote
                        )
                    )
                pass
            pass

        # Set the c-arrays
        for chan in range(chMin,chMax):
            idx = 128*vfat + chan

            # Check if it's possible to trim
            # If not, include the channel in the masks
            if ( abs(dict_trimVal[vfat][chan]) > 0x7f):
                cArray_Masks[idx] = 1 # True

            # Determine trim polarity
            # if dict_trimVal[vfat] >= 0 scurve is above the average, need negative trim polarity
            # if dict_trimVal[vfat] <  0 scurve is below the average, need positive trim polarity
            trimPol = 0x0
            if (dict_trimVal[vfat][chan] >= 0):
                trimPol = 0x1
                pass
            cArray_trimPol[idx] = trimPol

            # Store the trim config
            chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')
            chConfig.write('%i\t%i\t%i\t%i\t%i\t%i\n'%(
                vfat,
                dict_vfatID[vfat],
                chan,
                abs(dict_trimVal[vfat][chan]),
                trimPol,
                cArray_Masks[idx]))

            # Set the trim value
            cArray_trimVal[idx] = int(abs(dict_trimVal[vfat][chan]))
            pass
        pass

    # Close the config file
    chConfig.close()

    # Set the trim values
    print("Setting trim values for all channels")
    rpcResp = vfatBoard.setAllChannelRegisters(
                    chMask=cArray_Masks,
                    trimARM=cArray_trimVal,
                    trimARMPol=cArray_trimPol,
                    vfatMask=options.vfatmask,
                    debug=options.debug)

    if rpcResp != 0:
        raise Exception("RPC response was non-zero, setting trim values for all channels failed")
    
    #####################
    # TRIMDAC = Trimmed #
    #####################
    print("taking an scurve with the trim values set")
    # Scurve scan with trims set to the determined values
    filename_trimmed = "%s/SCurveData_Trimmed.root"%dirPath
    cmd = [ "ultraScurve.py",
            "--shelf=%i"%(options.shelf),
            "-s%d"%(options.slot),
            "-g%d"%(options.gtx),
            "--chMin=%i"%(options.chMin),
            "--chMax=%i"%(options.chMax),
            "--latency=%i"%(options.latency),
            "--mspl=%i"%(options.MSPL),
            "--nevts=%i"%(options.nevts),
            "--vfatmask=0x%x"%(options.vfatmask),
            "--filename=%s"%(filename_trimmed)
            ]
    # Debug Flag?
    #if options.debug:
    #    cmd.append("--debug")
    # Voltage or current pulse?
    if options.voltageStepPulse:
        cmd.append("--voltageStepPulse")
    else:
        cmd.append("--calSF=%i"%(options.calSF) )
    runCommand(cmd)

    print("s-curve with trim values set completed")

    if options.printSummary:
        # Get the initial fit results
        print("fitting results, this may take some time")
        fitResults_Trimmed = fitScanData(treeFileName=filename_trimmed, isVFAT3=True)
        print("fitting has completed")

        # Determine post trim settings
        dict_scurvePOIPerChan_PostTrim = { vfat:np.zeros(128) for vfat in range(0,24) }
        print("Analyzing the fit data to determine the trim values")
        for vfat in range(0,24):
            # skip masked vfats
            if (options.vfatmask >> vfat) & 0x1: 
                continue
            
            # Print a table
            print("| vfatN | chan | scurvePOI | avgScurvePOI | scurvePOIPostTrim | trimVal | trimPol | Note |")
            print("| :---: | :--: | :-------: | :----------: | :---------------: | :-----: | :-----: | :--- |")
            
            # Determine scurve point of interest by channel after trimming
            for chan in range(chMin,chMax):
                idx = 128*vfat + chan

                # Skip empty s-curves
                if fitResults_Trimmed[4][vfat][chan] < 0.1: 
                    continue # do not consider channels w/empty s-curves
                
                # store the position and mask negative scurve POI's
                dict_scurvePOIPerChan_PostTrim[vfat][chan] = int(round(fitResults_Trimmed[0][vfat][chan] - ztrim * fitResults_Trimmed[1][vfat][chan]))
        
                # Tell the user what we are doing
                chNote = " - "
                if ( abs(dict_trimVal[vfat][chan]) > 0x7f):
                    chNote = "Needed TrimVal Exceeds Range"
                    pass
                print("| %i | %i | %i | %i | %i | %i | %i | %s |"%(
                        vfat, 
                        chan,
                        dict_scurvePOIPerChan[vfat][chan],
                        array_avgScurvePOIPerVFAT[vfat],
                        dict_scurvePOIPerChan_PostTrim[vfat][chan],
                        abs(dict_trimVal[vfat][chan]),
                        int(dict_trimVal[vfat][chan] >= 0),
                        chNote
                        )
                    )
                pass # End loop over channels
            pass # End loop over vfats
        
        # Provide summary information
        print("| vfatN | numUnMaskedChan | avgScurvePOI | avgDeltaPreTrim | stdDevDeltaPreTrim | avgDeltaPostTrim | stdDevDeltaPostTrim |")
        print("| :---: | :-------------: | :----------: | :------------: | :----------------: | :--------------: | :-----------------: |")
        for vfat in range(0,24):
            # skip masked vfats
            if (options.vfatmask >> vfat) & 0x1: 
                continue
            
            avgDeltaPreTrim = np.mean(dict_trimVal[vfat])
            stdDevDeltaPreTrim = np.std(dict_trimVal[vfat])
            if array_avgScurvePOIPerVFAT[vfat] == -1:
                avgDeltaPostTrim = 0
                stdDevDeltaPostTrim = 0
            else:
                avgDeltaPostTrim = np.mean(
                        np.abs(
                            dict_scurvePOIPerChan_PostTrim[vfat] - array_avgScurvePOIPerVFAT[vfat] 
                            )
                        )
                stdDevDeltaPostTrim = np.std(
                        np.abs(
                            dict_scurvePOIPerChan_PostTrim[vfat] - array_avgScurvePOIPerVFAT[vfat] 
                            )
                        )
                pass

            print("| %i | %i | %i | %f | %f | %f | %f |"%(
                    vfat,
                    len(dict_scurvePOIPerChan_PostTrim[vfat][dict_scurvePOIPerChan_PostTrim[vfat] > 0]),
                    array_avgScurvePOIPerVFAT[vfat],
                    avgDeltaPreTrim,
                    stdDevDeltaPreTrim,
                    avgDeltaPostTrim,
                    stdDevDeltaPostTrim
                    )
                )
            pass
        pass # End print summary

    print("Trimming Completed")
