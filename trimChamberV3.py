#!/bin/env python
"""
Script to set trimdac values on a V3 chamber
By: Brian Dorney (brian.l.dorney@cern.ch)
"""

if __name__ == '__main__':
    from gempython.gemplotting.utils.anautilities import parseCalFile, parseArmDacCalFile
    from ctypes import *
    from gempython.gemplotting.fitting.fitScanData import fitScanData
    from gempython.tools.vfat_user_functions_xhal import *
    from gempython.utils.nesteddict import nesteddict as ndict
    from gempython.utils.wrappers import runCommand, envCheck
    from gempython.gemplotting.mapping.chamberInfo import chamber_config
    from gempython.vfatqc.utils.qcoptions import parser
    from gempython.vfatqc.utils.scanUtils import launchSCurve
    
    import datetime, subprocess, time
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
    parser.add_option("--mspl", type="int", dest = "MSPL", default = 3,
                      help="Specify MSPL. Must be in the range 0-7 (default is 3)", metavar="MSPL")
    parser.add_option("--printSummary", action="store_true", dest="printSummary",
                      help="Prints a summary table describing the results before and after trimming",
                      metavar="printSummary")
    parser.add_option("--trimPoints", type="string", dest="trimPoints", default="-63,0,63",
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

    # Get the calibration for the CFG_CAL_DAC register
    tuple_calInfo = parseCalFile(options.calFileCAL)
    calDac2Q_Slope = tuple_calInfo[0]
    calDac2Q_Intercept = tuple_calInfo[1]

    dict_func_scurveMeanVsThrDac = {}

    import ROOT as r

    # Make the ohKey
    ohKey = (options.shelf,options.slot,options.gtx)

    # Get the calibration for the CFG_THR_ARM_DAC register    
    if options.calFileARM is None:
        envCheck('DATA_PATH')
        dataPath = os.getenv('DATA_PATH')
        calFileBase = "{0}/{1}/calFile_CFG_THR_ARM_DAC_{1}".format(dataPath,chamber_config[ohKey])
        if os.path.isfile(calFileBase + ".root"):
            TFile_calInfo = r.TFile(calFileBase + ".root")
            for vfat in range(0,24):
                for key in TFile_calInfo.GetDirectory("VFAT{0}".format(vfat)).GetListOfKeys():
                    if "func_ScurveMean_vs_CFG_THR_ARM_DAC_" in key.GetName() and "_vfatN{0}_".format(vfat) in key.GetName():
                        dict_func_scurveMeanVsThrDac[vfat] = TFile_calInfo.GetDirectory("VFAT{0}".format(vfat)).Get(key.GetName())
                        break
        elif os.path.isfile(calFileBase + ".txt"):            
            tuple_calInfo = parseArmDacCalFile(calFileBase + ".txt")
            for vfat in range(0,24):
                dict_func_scurveMeanVsThrDac[vfat] = r.TF1("func_scurveMeanVsThrDac_vfat%d"%(vfat),"[0]*x^4+[1]*x^3+[2]*x^2+[3]*x+[4]")
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(0,tuple_calInfo[0][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(1,tuple_calInfo[1][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(2,tuple_calInfo[2][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(3,tuple_calInfo[3][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(4,tuple_calInfo[4][vfat])
        else:
            print("Needed CFG_THR_ARM_DAC calibration file not found in the expected location and not provided via --calFileARM.")
            exit(os.EX_USAGE)
    else:
        if options.calFileARM[-4:] == ".txt":
            tuple_calInfo = parseArmDacCalFile(options.calFileARM)
            for vfat in range(0,24):
                dict_func_scurveMeanVsThrDac[vfat] = r.TF1("func_scurveMeanVsThrDac_vfat%d"%(vfat),"[0]*x^4+[1]*x^3+[2]*x^2+[3]*x+[4]")
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(0,tuple_calInfo[0][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(1,tuple_calInfo[1][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(2,tuple_calInfo[2][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(3,tuple_calInfo[3][vfat])
                dict_func_scurveMeanVsThrDac[vfat].SetParameter(4,tuple_calInfo[4][vfat])
        elif options.calFileARM[-5:] == ".root":
            TFile_calInfo = r.TFile(options.calFileARM)
            for vfat in range(0,24):
                for key in TFile_calInfo.GetDirectory("VFAT{0}".format(vfat)).GetListOfKeys():
                    if "func_ScurveMean_vs_CFG_THR_ARM_DAC_" in key.GetName() and "_vfatN{0}_".format(vfat) in key.GetName():
                        dict_func_scurveMeanVsThrDac[vfat] = TFile_calInfo.GetDirectory("VFAT{0}".format(vfat)).Get(key.GetName())
                        break

    chMin = options.chMin
    chMax = options.chMax + 1

    if options.dirPath == None:
        envCheck('DATA_PATH')
        dataPath = os.getenv('DATA_PATH')
        startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
        print(startTime)
        dirPath = '%s/%s/trim'%(dataPath,chamber_config[ohKey])
        runCommand( ["unlink","%s/current"%dirPath] )
        runCommand( ['mkdir','-p','%s/%s'%(dirPath,startTime)])
        runCommand( ["ln","-s",'%s/%s'%(dirPath,startTime),'%s/current'%dirPath] )
        dirPath = '%s/%s'%(dirPath,startTime)
    else: 
        dirPath = options.dirPath
        pass
  
    # Declare the hardware board
    from gempython.vfatqc.utils.qcutilities import getCardName
    cardName = getCardName(options.shelf,options.slot)
    vfatBoard = HwVFAT(cardName, options.gtx, options.debug)
    print 'opened connection'
    
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
    else:
        vfatBoard.setVFATThresholdAll(mask=options.vfatmask, vt1=options.armDAC)
        
    # Get all chip IDs
    vfatIDvals = vfatBoard.getAllChipIDs(options.vfatmask)

    # Get global arm dac value
    vals = vfatBoard.readAllVFATs("CFG_THR_ARM_DAC", options.vfatmask)
    dict_thrArmDacPerVFAT =  dict(map(lambda slotID: (slotID, vals[slotID]&0xff),range(0,24)))

    # Make the cArrays
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
        isZombie = True
        if os.path.isfile(filename):
            scurveRawFile = r.TFile(filename,"READ")
            isZombie = scurveRawFile.IsZombie()

        if not isZombie:
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
                        cardName = cardName,
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
        else:
            print("file %s either does not exist, or is a zombie"%filename)
            print("Going to try to take an scurve at this (trimVal,trimPol) = (%d,%d) setting"%(trimVal,trimPol))
            # Set arrays for trimVal and trimPol
            for idx in range(0,3072):
                cArray_trimVal[idx] = trimVal
                cArray_trimPol[idx] = trimPol

            # Scurve scan at this (trimVal, trimPol) setting
            launchSCurve(
                    calSF = options.calSF,
                    cardName = cardName,
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

    # Create the output file which will store the channel configurations
    chConfig = open("%s/chConfig.txt"%dirPath,"w")
    chConfig.write('vfatN/I:vfatID/I:vfatCH/I:trimDAC/I:trimPolarity/I:mask/I\n')

    # Create the output file which will store the trim data 
    outFile = r.TFile("%s/TrimData.root"%(dirPath),"RECREATE")
    
    # Setup the output TTree
    thisTime = int(time.time())
    from gempython.vfatqc.utils.treeStructure import gemDacCalTreeStructure
    trimDacArmTree = gemDacCalTreeStructure(
            name='trimDacArmTree',
            nameX='scurve mean #left(fC#right)',
            nameY='ARM_TRIM_AMPLITUDE',
            isGblDac=False,
            description='Tree holding arming comparator trim data')
    trimDacArmTree.setDefaults(options, thisTime)

    calDacCalTree = gemDacCalTreeStructure(
            name='calDacCalibration',
            nameX='CFG_CAL_DAC',
            nameY='charge #left(fC#right)',
            storeRoot=True,
            description='Tree holding CFG_CAL_DAC Calibration')
    calDacCalTree.setDefaults(options, thisTime)

    armDacCalTree = gemDacCalTreeStructure(
            name='thrArmDacCalibration',
            nameX='CFG_THR_ARM_DAC',
            nameY='scurve mean #left(fC#right)',
            storeRoot=True,
            description='Tree holding CFG_THR_ARM_DAC Calibration;')
    armDacCalTree.setDefaults(options, thisTime)

    print("Determining trimDAC to fC Calibration")
    dict_cal_trimDAC2fC_graph = ndict() # dict_cal_trimDAC2fC[vfat][chan] = TGraphErrors object
    dict_cal_trimDAC2fC_func = ndict() # dict_cal_trimDAC2fC[vfat][chan] = TF1 object
    for vfat in range(0,24):
        func_charge_vs_calDac = r.TF1(
                "func_charge_vs_calDac_vfat%d"%(vfat),
                "[0]*x+[1]",
                calDac2Q_Slope[vfat]*253+calDac2Q_Intercept[vfat],
                calDac2Q_Slope[vfat]*1+calDac2Q_Intercept[vfat])
        func_charge_vs_calDac.SetParameter(0,calDac2Q_Slope[vfat])
        func_charge_vs_calDac.SetParameter(1,calDac2Q_Intercept[vfat])
        calDacCalTree.fill(
                func_dacFit=func_charge_vs_calDac,
                vfatID = vfatIDvals[vfat],
                vfatN = vfat)
        
        armDacCalTree.fill(
                func_dacFit=dict_func_scurveMeanVsThrDac[vfat],
                vfatID = vfatIDvals[vfat],
                vfatN = vfat)

        # Determine scurve point of interest by channel
        print("fitting trimDAC vs. scurve mean for vfat %d"%vfat)
        for chan in range(chMin,chMax):
            #print("fitting trimDAC vs. scurve mean for vfat %d chan"%(vfat,chan))
            idx = 128*vfat + chan

            # Declare the TGraphErrors storing the trimDAC calibration for this ARM DAC
            g_TrimDAC_vs_scurveMean = r.TGraphErrors(len(dict_scurveFitResults))
            g_TrimDAC_vs_scurveMean.SetName("gCal_trimARM_vs_scurveMean_vfat%d_chan%d_gblArmDAC%d"%(vfat,chan,dict_thrArmDacPerVFAT[vfat]))
            g_TrimDAC_vs_scurveMean.SetMarkerStyle(24)
            g_TrimDAC_vs_scurveMean.SetTitle("VFAT{0} Channel {1};scurve mean #left(fC#right);trimDAC".format(vfat, chan))

            # Declare the fit function 
            func_TrimDAC_vs_scurveMean = r.TF1(
                    "func_TrimDAC_vs_scurveMean_vfat%d_chan%d_gblArmDAC%d"%(vfat,chan,dict_thrArmDacPerVFAT[vfat]),
                    "[0]*x+[1]",
                    min(listOfTrimPoints),
                    max(listOfTrimPoints))
            
            numValidChanFits = 0
            for idx,trimPt in enumerate(dict_scurveFitResults.keys()):
                if trimPt[1] > 0: # negative trimVal
                    trimVal = trimPt[0] * -1
                else: # positive trimVal
                    trimVal = trimPt[0]

                g_TrimDAC_vs_scurveMean.SetPoint(
                        idx,
                        dict_scurveFitResults[trimPt][0][vfat][chan],
                        trimVal)

                # Store output trim data
                trimDacArmTree.fill(
                        dacValX = dict_scurveFitResults[trimPt][0][vfat][chan],
                        dacValX_Err = dict_scurveFitResults[trimPt][1][vfat][chan],
                        dacValY = trimVal,
                        vfatCH = chan,
                        vfatID = vfatIDvals[vfat],
                        vfatN = vfat)

                # Store the number of valid scurve fits for this channel
                numValidChanFits+=dict_scurveFitResults[trimPt][6][vfat][chan]

            if numValidChanFits >=2: # Can Make a line
                try:
                    # Fit g_TrimDAC_vs_scurveMean
                    fitResult = g_TrimDAC_vs_scurveMean.Fit(func_TrimDAC_vs_scurveMean, "QRS")
                    fitValid = fitResult.IsValid()
                    if not fitValid:
                        print("trimChamberV3.py main(): found trimDAC fit of vfat %d chan %d to be not valid!!"%(vfat,chan))
                        cArray_trimVal[128*vfat+chan] = 0
                        cArray_trimPol[128*vfat+chan] = 0
                    else:
                        # Determine the trim value and polarity to shift this channel to the
                        # global arm dac threshold (CFG_THR_ARM_DAC) for this VFAT
                        armDacCharge = dict_func_scurveMeanVsThrDac[vfat].Eval(dict_thrArmDacPerVFAT[vfat])
                        trimVal = func_TrimDAC_vs_scurveMean.Eval(armDacCharge)
                        if trimVal > 0:
                            cArray_trimPol[128*vfat+chan] = 0
                        else:
                            trimVal = abs(trimVal)
                            cArray_trimPol[128*vfat+chan] = 1

                        if trimVal > 0x3F: # If trimVal is over the max, reset to the max
                            trimVal = 0x3F
                        cArray_trimVal[128*vfat+chan] = int(trimVal)
                except ReferenceError:
                    print("trimChamberV3.py main(): TFitResult is a null pointer, skipping vfat %d chan %d!!"%(vfat,chan))
                    cArray_trimVal[128*vfat+chan] = 0
                    cArray_trimPol[128*vfat+chan] = 0
            else:
                cArray_trimVal[128*vfat+chan] = 0
                cArray_trimPol[128*vfat+chan] = 0

            dict_cal_trimDAC2fC_graph[vfat][chan] = g_TrimDAC_vs_scurveMean
            dict_cal_trimDAC2fC_func[vfat][chan] = func_TrimDAC_vs_scurveMean
            
            # Write Channel Configuration
            chConfig.write('%d\t%d\t%d\t%d\t%d\t%d\n'%(
                    vfat,
                    vfatIDvals[vfat],
                    chan,
                    cArray_trimVal[128*vfat+chan],
                    cArray_trimPol[128*vfat+chan],
                    0)
                )

    # Write output
    for vfat in range(0,24):
        dirVFAT = outFile.mkdir("VFAT%i"%vfat)
        for chan in range(chMin,chMax):
            dirChan = dirVFAT.mkdir("chan%i"%chan)
            dirChan.cd()
            dict_cal_trimDAC2fC_graph[vfat][chan].Write()
            dict_cal_trimDAC2fC_func[vfat][chan].Write()
    outFile.cd()
    trimDacArmTree.write()
    calDacCalTree.write()
    armDacCalTree.write()

    # Now take an scurve using the new trim settings
    filename = "%s/SCurveData_Trimmed.root"%(dirPath)

    print("taking an scurve with final trimVal and trimPol settings")
    # Scurve scan at this (trimVal, trimPol) setting
    launchSCurve(
            calSF = options.calSF,
            cardName = cardName,
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
