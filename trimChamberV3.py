#!/bin/env python
"""
Script to set trimdac values on a V3 chamber
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

if __name__ == '__main__':
    from gempython.gemplotting.utils.anautilities import getEmptyPerVFATList, parseCalFile, rejectOutliersMADOneSided
    from array import array
    from ctypes import *
    from gempython.gemplotting.fitting.fitScanData import fitScanData
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import runCommand, envCheck
    from gempython.gemplotting.mapping.chamberInfo import chamber_config, chamber_vfatDACSettings
    from gempython.vfatqc.qcoptions import parser
    from gempython.vfatqc.qcutilities import launchSCurve
    
    import datetime, subprocess, sys
    import numpy as np
    import os
   
    parser.add_option("--armDAC", type="int", dest = "armDAC", default = 100,
                      help="CFG_THR_ARM_DAC value to write to all VFATs", metavar="armDAC")
    parser.add_option("--calFileCAL", type="string", dest="calFileCAL", default=None,
                      help="File specifying CAL_DAC to fC equations per VFAT",
                      metavar="calFileCAL")
    parser.add_option("--calFileARM", type="string", dest="calFileARM", default=None,
                      help="File specifying THR_ARM_DAC to fC equations per VFAT",
                      metavar="calFileARM")
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
    parser.add_option("--trimPoints" type="string", dest="trimPoints", default="-127,0,127",
                      help="comma separated list of trim values to use in trimming, a set of scurves will be taken at each point", metavar="trimPoints")
    parser.add_option("--vfatConfig", type="string", dest="vfatConfig", default=None,
                      help="Specify file containing VFAT settings from anaUltraThreshold", metavar="vfatConfig")
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    (options, args) = parser.parse_args()
   
    if options.calFileCAL is None:
        print("You must provide the calibration for the CFG_CAL_DAC register")
        print("Please relaunch with the --calFileCAL argument")
        exit(os.EX_USAGE)
        pass

    if options.calFileARM is None:
        print("You must provide the calibration for the CFG_THR_ARM_DAC register")
        print("Please relaunch with the --calFileARM argument")
        exit(os.EX_USAGE)
        pass

    # Get the calibration for the CFG_THR_ARM_DAC register
    tuple_calInfo = parseCalFile(options.calFileARM)
    thrArmDac2Q_Slope = tuple_calInfo[0]
    thrArmDac2Q_Intercept = tuple_calInfo[1]

    chMin = options.chMin
    chMax = options.chMax + 1

    if options.dirPath == None: 
        envCheck('DATA_PATH')
        dataPath = os.getenv('DATA_PATH')
        startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
        print(startTime)
        #dirPath = '%s/%s/trim/z%f'%(dataPath,chamber_config[options.gtx],ztrim)
        dirPath = '%s/%s/'%(dataPath,chamber_config[options.gtx])
        runCommand( ["unlink","%s/current"%dirPath] )
        runCommand( ['mkdir','-p','%s/%s'%(dirPath,startTime)])
        runCommand( ["ln","-s",'%s/%s'%(dirPath,startTime),'%s/current'%dirPath] )
        dirPath = '%s/%s'%(dirPath,startTime)
    else: 
        dirPath = options.dirPath
        pass
  
    # Declare the hardware board and bias all vfats
    if options.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    vfatBoard = HwVFAT(options.cardName, options.gtx, options.debug)
    print 'opened connection'
    
    if options.gtx in chamber_vfatDACSettings.keys():
        print("Configuring VFATs with chamber_vfatDACSettings dictionary values")
        for key in chamber_vfatDACSettings[options.gtx]:
            vfatBoard.paramsDefVals[key] = chamber_vfatDACSettings[options.gtx][key]
            pass
        pass
    vfatBoard.paramsDefVals['CFG_THR_ARM_DAC']=options.armDAC
    vfatBoard.biasAllVFATs(options.vfatmask)
    print('biased VFATs')
    
    import ROOT as r
    if options.vfatConfig is not None:
        try:
            print 'Configuring VFAT Registers based on %s'%options.vfatConfig
            vfatTree = r.TTree('vfatTree','Tree holding VFAT Configuration Parameters')
            vfatTree.ReadFile(options.vfatConfig)
            
            for event in vfatTree :
                # Skip masked vfats
                if (options.vfatmask >> int(event.vfatN)) & 0x1:
                    continue
                    
                # Write CFG_THR_ARM_DAC
                print('Set link %d VFAT%d CFG_THR_ARM_DAC to %i'%(options.gtx,event.vfatN,event.vt1))
                vfatBoard.setVFATThreshold(chip=int(event.vfatN), vt1=int(event.vt1))
        except IOError as e:
            print '%s does not seem to exist or is not readable'%options.filename
            print e
        
        vals  = vfatBoard.readAllVFATs("CFG_THR_ARM_DAC", options.vfatmask)
        dict_thrArmDacPerVFAT =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))

    # Make the cArrays
    #cArray_Masks = (c_uint32 * 3072)()
    cArray_trimVal = (c_uint32 * 3072)()
    cArray_trimPol = (c_uint32 * 3072)()
    
    ###############
    # Take scurves at each trimPoint
    ###############
    listOfTrimPoints = [ int(trimVal) for trimVal in options.trimPoints.split(",") ]
    dict_scurveFiles = {} # Key -> (trimVal, trimPol); value -> string that is scurve filename
    dict_scurveFitResults = {} # Key -> (trimVal, trimPol); value -> scanFitResults from ScanDataFitter class
    for trimVal in listOfTrimPoints:
        # Determine trim polarity and amplitude register values
        # ARM_TRIM_POLARITY 0 -> positive; 1 -> negative
        if trimVal >= 0:
            trimPol = 0
        else:
            trimPol = 1
            trimVal = abs(trimVal)

        # Check if an scurve at this (trimVal, trimPol) was already taken
        filename = "%s/SCurveData_trimdac%d_trimPol%d.root"%(dirPath,trimVal,trimPol)
        scurveRawFile = r.TFile(filename,"READ")

        try:
            thisTree = scurveRawFile.scurveTree
        except AttributeError as error:
            print("caught exception %s"%error)
            print("Going to try to take an scurve at this (trimVal,trimPol) = (%d,%d) setting"%(trimVal,trimPol))
            # Set arrays for trimVal and trimPol
            for idx in range(0,3072):
                cArray_trimVal[idx] = trimVal
                cArray_trimPol[idx] = trimPol

            # Scurve scan at this (trimVal, trimPol) setting
            launchSCurve(
                    calSF = options.calSF,
                    cardName = options.cardName,
                    chMax = options.chMax,
                    chMin = options.chMin,
                    debug = options.debug,
                    filename = filename,
                    latency = options.latency,
                    link = options.gtx,
                    mspl = options.MSPL,
                    nevts = options.nevts,
                    setChanRegs = True,
                    trimARM = cArray_trimVal,
                    trimARMPol = cArray_trimPol,
                    vfatmask = options.vfatmask,
                    voltageStepPulse = options.voltageStepPulse)
            print("scurve finished")
        dict_scurveFiles[(trimVal,trimPol)] = filename
        print("fitting results, this may take some time")
        dict_scurveFitResults[(trimVal, trimPol)] = fitScanData(treeFileName=filename, isVFAT3=True, calFileName=options.calFileCAL)
        print("fitting has completed")
    print("All trim points have been taken, processing")

    # Need to get the CFG_THR_ARM_DAC value per VFAT
    #import ROOT as r
    #import root_numpy as rp
    #list_bNames = [ 'vfatN', 'vthr' ]
    #fileUntrimmed = r.TFile(filename_untrimmed,"READ")
    #array_thrArmDacPerVFAT = rp.tree2array(tree=fileUntrimmed.scurveTree, branches=list_bNames)
    #array_thrArmDacPerVFAT = np.unique(array_thrArmDacPerVFAT,axis=0)
    #dict_thrArmDacPerVFAT = dict(map(lambda vfatN:(array_thrArmDacPerVFAT['vfatN'][vfatN], array_thrArmDacPerVFAT['vthr'][vfatN]), range(0,len(array_thrArmDacPerVFAT))))

    # Create the output file which will store the channel configurations
    chConfig = open("%s/chConfig.txt"%dirPath,"w")
    chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')

    # Create the output file which will 

    print("Determining trimDAC to fC Calibration")
    dict_cal_trimDAC2fC_graph = ndict() # dict_cal_trimDAC2fC[vfat][chan] = TGraphErrors object
    dict_cal_trimDAC2fC_func = ndict() # dict_cal_trimDAC2fC[vfat][chan] = TF1 object
    for vfat in range(0,24):
        # skip masked vfats
        if (options.vfatmask >> vfat) & 0x1: 
            continue
        
        # Determine scurve point of interest by channel
        print("fitting trimDAC vs. scurve mean for vfat %d"%vfat)
        for chan in range(chMin,chMax):
            idx = 128*vfat + chan

            g_TrimDAC_vs_scurveMean = r.TGraphErrors(len(dict_scurveFitResults))
            g_TrimDAC_vs_scurveMean.SetName("gCal_trimARM_vs_scurveMean_vfat%d_chan%d_gblArmDAC%d"%(vfat,chan,dict_thrArmDacPerVFAT[vfat]))
            
            for idx,trimPt in enumerate(dict_scurveFitResults.keys()):
                if trimPt[1] > 0: # negative trimVal
                    trimVal = trimPt[0] * -1
                else: # positive trimVal
                    trimVal = trimPt[0]

                g_TrimDAC_vs_scurveMean.SetPoint(
                        idx,
                        dict_scurveFitResults[trimPt][0][vfat][chan],
                        trimVal)

                g_TrimDAC_vs_scurveMean.SetPointError(
                        idx,
                        dict_scurveFitResults[trimPt][1][vfat][chan],
                        0)

            # Fit g_TrimDAC_vs_scurveMean using y=mx+b
            func_TrimDAC_vs_scurveMean = r.TF1(
                    "func_TrimDAC_vs_scurveMean_vfat%d_chan%d_gblArmDAC%d"%(vfat,chan,dict_thrArmDacPerVFAT[vfat]),
                    "[0]*x+[1]",
                    min(listOfTrimPoints),
                    max(listOfTrimPoints))
            g_TrimDAC_vs_scurveMean.Fit(func_TrimDAC_vs_scurveMean, "RQ")

            # Determine the trim value and polarity to shift this channel to the 
            # global arm dac threshold (CFG_THR_ARM_DAC) for this VFAT
            armDacCharge = thrArmDac2Q_Slope[vfat] * dict_thrArmDacPerVFAT[vfat] + thrArmDac2Q_Intercept[vfat]
            trimVal = g_TrimDAC_vs_scurveMean.Eval( armDacCharge )
            if trimVal > 0:
                cArray_trimPol[128*vfat+chan] = 0
            else:
                trimVal = abs(trimVal)
                cArray_trimPol[128*vfat+chan] = 1

            if trimVal > 0x7F: # If trimVal is over the max, reset to the max
                trimVal = 0x7F
            cArray_trimVal[128*vfat+chan] = trimVal

            dict_cal_trimDAC2fC_graph[vfat][chan] = g_TrimDAC_vs_scurveMean
            dict_cal_trimDAC2fC_func[vfat][chan] = func_TrimDAC_vs_scurveMean

    # Now take an scurve using the new trim settings
    filename = "%s/SCurveData_Trimmed.root"%(dirPath)

    print("taking an scurve with final trimVal and trimPol settings")
    # Scurve scan at this (trimVal, trimPol) setting
    launchSCurve(
            calSF = options.calSF,
            cardName = options.cardName,
            chMax = options.chMax,
            chMin = options.chMin,
            debug = options.debug,
            filename = filename,
            latency = options.latency,
            link = options.gtx,
            mspl = options.MSPL,
            nevts = options.nevts,
            setChanRegs = True,
            trimARM = cArray_trimVal,
            trimARMPol = cArray_trimPol,
            vfatmask = options.vfatmask,
            voltageStepPulse = options.voltageStepPulse)
    print("scurve finished")
    print("Trimming procedure completed")
