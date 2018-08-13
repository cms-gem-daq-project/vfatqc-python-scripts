#!/bin/env python

if __name__ == '__main__':
    """
    Script to test sbit mapping and trigger rate
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    from array import array
    from ctypes import *

    from gempython.tools.vfat_user_functions_xhal import *
    
    from gempython.vfatqc.qcoptions import parser

    parser.add_option("--calSF", type="int", dest = "calSF", default = 0,
                      help="V3 electroncis only. Value of the CFG_CAL_FS register", metavar="calSF")
    parser.add_option("-f", "--filename", type="string", dest="filename", default="SBitData.root",
                      help="Specify Output Filename", metavar="filename")
    parser.add_option("--latency", type="int", dest = "latency", default = 37,
                      help="Specify Latency", metavar="latency")
    parser.add_option("--rates", type="string", dest = "rates", default = "1e3,1e4,1e5,1e6,1e7",
                      help="Comma separated list of floats that specifies the pulse rates to be considered",
                      metavar="rates")
    parser.add_option("--time", type="int", dest="time", default = 1000,
                      help="Acquire time per point in milliseconds", metavar="time")
    parser.add_option("--vcal", type="int", dest="vcal",
                      help="Height of CalPulse in DAC units for all VFATs", metavar="vcal", default=250)
    parser.add_option("--voltageStepPulse", action="store_true",dest="voltageStepPulse", 
                      help="V3 electronics only. Calibration Module is set to use voltage step pulsing instead of default current pulse injection", 
                      metavar="voltageStepPulse")
    (options, args) = parser.parse_args()

    import ROOT as r
    filename = options.filename
    myF = r.TFile(filename,'recreate')
    
    import subprocess,datetime,time
    startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
    print startTime
    Date = startTime

    # Track the current pulse
    isCurrentPulse = (not options.voltageStepPulse)

    # Setup the output TTree
    #from gempython.vfatqc.treeStructure import gemTreeStructure
    #gemData = gemTreeStructure('scurveTree','Tree Holding CMS GEM SCurve Data')
    #gemData.setDefaults(options, int(time.time()))
    sbitDataTree = r.TTree("sbitDataTree","Tree Holding SBIT Mapping and Rate Data")

    ratePulsed = array( 'f', [ 0 ] )
    sbitDataTree.Branch( 'ratePulsed', ratePulsed, 'ratePulsed/F' )

    rateObservedCTP7 = array( 'f', [ 0 ] )
    sbitDataTree.Branch( 'rateObservedCTP7', rateObservedCTP7, 'rateObservedCTP7/F' )

    rateObservedFPGA = array( 'f', [ 0 ] )
    sbitDataTree.Branch( 'rateObservedFPGA', rateObservedFPGA, 'rateObservedFPGA/F' )

    rateObservedVFAT = array( 'f', [ 0 ] )
    sbitDataTree.Branch( 'rateObservedVFAT', rateObservedVFAT, 'rateObservedVFAT/F' )

    sbitValid = array( 'i', [ 0 ] )
    sbitDataTree.Branch( 'isValid', sbitValid, 'isValid/I' )

    sbitSize = array( 'i', [ 0 ] )
    sbitDataTree.Branch( 'sbitClusterSize', sbitSize, 'sbitClusterSize/I' )

    sbitObserved = array( 'i', [ 0 ] ) #SBIT Observed
    sbitDataTree.Branch( 'vfatSBIT', sbitObserved, 'vfatSBIT/I' )
    
    vfatCH = array( 'i', [ 0 ] ) # Channel Pulsed
    sbitDataTree.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    
    vfatID = array( 'i', [-1] )
    sbitDataTree.Branch( 'vfatID', vfatID, 'vfatID/I' ) #Hex Chip ID of VFAT

    vfatN = array( 'i', [ -1 ] ) # VFAT Pulsed
    sbitDataTree.Branch( 'vfatN', vfatN, 'vfatN/I' )
    
    vfatObserved = array( 'i', [ 0 ] ) #VFAT Observed
    sbitDataTree.Branch( 'vfatObserved', vfatObserved, 'vfatObserved/I')

    # Set vfatmask
    mask = options.vfatmask

    # Determine rates and L1Aintervals
    from gempython.vfatqc.qcutilities import calcL1Ainterval
    dictRateMap = { float(rate):calcL1Ainterval(float(rate)) for rate in options.rates.split(",")}

    # Open rpc connection to hw
    if options.cardName is None:
        print("you must specify the --cardName argument")
        exit(os.EX_USAGE)

    vfatBoard = HwVFAT(options.cardName, options.gtx, options.debug)
    print 'opened connection'

    # Check options
    from gempython.vfatqc.qcutilities import inputOptionsValid
    if not inputOptionsValid(options, vfatBoard.parentOH.parentAMC.fwVersion):
        exit(os.EX_USAGE)

    if vfatBoard.parentOH.parentAMC.fwVersion < 3:
        print("Parent AMC Major FW Version: %i"%(vfatBoard.parentOH.parentAMC.fwVersion))
        print("Only implemented for v3 electronics, exiting")
        sys.exit(os.EX_USAGE)

    # Set relevant parameters
    vfatBoard.setVFATCalHeightAll(mask, options.vcal, currentPulse=isCurrentPulse)
    #vfatBoard.setVFATLatencyAll(mask=options.vfatmask, lat=options.latency, debug=options.debug)
    vfatBoard.setVFATMSPLAll(mask, options.MSPL, options.debug)

    # Get chip parameters
    # placeholder

    # setup c-array for checking mapping
    posPerEvt=8 #8 Sbit clusters will be readout per injected calpulse
    posPerChan = posPerEvt * options.nevts
    posPerVFAT = 128 * posPerChan
    scanDataMappingSizeNet = posPerVFAT * 24
    scanDataMapping = (c_uint32 * scanDataMappingSizeNet)()

    # setup c-arrays for checking rate
    scanDataCTP7Rate = (c_uint32 * 3072)()
    scanDataFPGARate = (c_uint32 * 3072)()
    scanDataVFATRate = (c_uint32 * 3072)()

    # Determine time for the rate test 
    #totalTime = (options.time / 1000) * 3072 * (1 / 3600)
    #print("I expect this sbit rate test will take: %f hours"%totalTime)
    #
    #bInputUnderstood=False
    #performTest=raw_input("Do you want to continue? (yes/no)")
    #while(not bInputUnderstood):
    #    performTest=performTest.upper()
    #    if performTest == "NO":
    #        print("Okay, exiting!")
    #        print("Please run again and change the '--time' argument to be a smaller valu")
    #        sys.exit(os.EX_USAGE)
    #    elif performTest == "YES":
    #        bInputUnderstood = True
    #        break;
    #    else:
    #        performTest=raw_input("input not understood, please enter 'yes' or 'no'")

    # Check Sbit Mapping and Rate
    for rate,L1Ainterval in dictRateMap.iteritems():
        if(L1Ainterval > 0xffff or L1Ainterval < 0x0):
            print("L1Ainterval {0} calculated from rate {1} Hz is out of bounds, acceptable limits are [0x0000, 0xFFFF]".format(hex(L1Ainterval),rate))
        
        #print("Checking sbit mapping")
        #rpcResp = vfatBoard.parentOH.checkSbitMappingWithCalPulse(calSF=options.calSF,currentPulse=isCurrentPulse,L1Ainterval=L1Ainterval,mask=mask,nevts=options.nevts,outData=scanDataMapping,pulseDelay=options.pDel)

        #print("len(scanDataMapping) = {0}".format(len(scanDataMapping)))

        #print("Storing sbit mapping information")
        #print("| idx | vfatN | chan | chanPulsed | sbitObs | vfatPulsed | vfatOBs | isValid | size | rawData |")
        #print("| --- | ----- | ---- | ---------- | ------- | ---------- | ------- | ------- | ---- | ------- |")
        #if rpcResp == 0:
        #    for vfat in range(0,24):
        #        for chan in range(0,128):
        #            for evt in range(0,options.nevts):
        #                for cluster in range(0,8):
        #                    idx = vfat * posPerVFAT + chan * posPerChan + evt * posPerEvt + cluster

        #                    vfatCH[0] = (scanDataMapping[idx]) & 0xFF
        #                    sbitObserved[0] = (scanDataMapping[idx] >> 8) & 0xFF
        #                    vfatN[0] = (scanDataMapping[idx] >> 16) & 0x1F
        #                    vfatObserved[0] = (scanDataMapping[idx] >> 21) & 0x1F
        #                    sbitValid[0] = (scanDataMapping[idx] >> 26) & 0x1
        #                    sbitSize[0] = (scanDataMapping[idx] >> 27) & 0x7
        #                    #vfatID[0]

        #                    if( scanDataMapping[idx] > 0 ):
        #                        print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} |".format(
        #                            idx,
        #                            vfat,
        #                            chan,
        #                            vfatCH[0],
        #                            sbitObserved[0],
        #                            vfatN[0],
        #                            vfatObserved[0],
        #                            sbitValid[0],
        #                            sbitSize[0],
        #                            hex(scanDataMapping[idx]))
        #                            )

        #                    sbitDataTree.Fill()
        
        rpcResp = vfatBoard.parentOH.checkSbitRateWithCalPulse(
                calSF=options.calSF, 
                currentPulse=isCurrentPulse,
                mask=mask,
                outDataCTP7Rate=scanDataCTP7Rate,
                outDataFPGARate=scanDataFPGARate,
                outDataVFATRate=scanDataVFATRate,
                pulseDelay=options.pDel,
                pulseRate=int(rate),
                waitTime=options.time)

        if rpcResp == 0:
            print("Storing sbit mapping information")
            print("| idx | vfatN | chan | ratePulsed | rateCTP7 | rateFPGA | rateVFAT |")
            print("| --- | ----- | ---- | ---------- | -------- | -------- | -------- |")
            for vfat in range(0,24):
                for chan in range(0,128):
                    idx=128*vfat+chan

                    ratePulsed[0]=rate
                    rateObservedCTP7[0]=scanDataCTP7Rate[idx]
                    rateObservedFPGA[0]=scanDataFPGARate[idx]
                    rateObservedVFAT[0]=scanDataVFATRate[idx]
                    vfatCH[0]=chan
                    #vfatID[0]=#placeholder
                    vfatN[0] = vfat

                    print("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
                        idx,
                        vfat,
                        chan,
                        rate,
                        scanDataCTP7Rate[idx],
                        scanDataFPGARate[idx],
                        scanDataVFATRate[idx])
                        )
                    
                    sbitDataTree.Fill()

    myF.cd()
    sbitDataTree.Write()
    myF.Close()
