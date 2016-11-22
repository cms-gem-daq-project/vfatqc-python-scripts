#!/usr/bin/env python

import sys, os, random, time
sys.path.append('${GEM_PYTHON_PATH}')

import uhal
from rate_calculator import rateConverter
from glib_user_functions_uhal import *
from optohybrid_user_functions_uhal import *
from vfat_functions_uhal import *

Passed = '\033[92m   > Passed... \033[0m'
Failed = '\033[91m   > Failed... \033[0m'

def txtTitle(str):
    print '\033[1m' + str + '\033[0m'
    return

class VFAT_SCAN_PARAMS:
    def __init__(self,
                 thresh_abs=0.1,thresh_rel=0.05,thresh_min=0,thresh_max=254,
                 lat_abs=0.7,lat_min=0,lat_max=254,
                 nev_thresh=3000,nev_lat=3000,
                 nev_scurve=1000,nev_trim=1000,
                 vcal_min=0,vcal_max=254,
                 max_trim_it=26,
                 chan_min=0,chan_max=128,
                 def_dac=16):
        self.THRESH_ABS      = thresh_abs
        self.THRESH_REL      = thresh_rel
        self.THRESH_MIN      = thresh_min
        self.THRESH_MAX      = thresh_max
        self.LAT_ABS         = lat_abs
        self.LAT_MIN         = lat_min
        self.LAT_MAX         = lat_max
        self.N_EVENTS_THRESH = nev_thresh
        self.N_EVENTS_LAT    = nev_lat
        self.N_EVENTS_SCURVE = nev_scurve
        self.N_EVENTS_TRIM   = nev_trim
        self.VCAL_MIN        = vcal_min
        self.VCAL_MAX        = vcal_max
        self.MAX_TRIM_IT     = max_trim_it
        self.CHAN_MIN        = chan_min
        self.CHAN_MAX        = chan_max
        self.DAC_DEF         = def_dac

        return

class VFATSCurveTools:
    """
    This set of tools provides functionality to produce S-Curve results for VFAT2 chips
    @author: Hugo DeWitt
    @modifiedby: Christine McClean
    Jared Sturdy - sturdy@cern.ch (Adapted for uHAL)
    """

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    def __init__(self, glib, slot, gtx, vfat, chipID, params, debug=False):
        """
        """
        self.glib   = glib
        self.slot   = slot
        self.gtx    = gtx
        self.vfat   = vfat
        self.chipID = chipID
        self.params = params
        self.debug  = debug

        if vfat not in range(0,24):
            print "Invalid VFAT specified %d is no in [0,23]"%(vfat)
            sys.exit(0)
            pass

        self.TotVCal = {}
        self.TotVCal["0"] = []
        self.TotVCal["16"] = []
        self.TotVCal["31"] = []
        self.TotFoundVCal = []

        self.VCal_ref  = {}
        self.VCal_ref["0"]   = 0
        self.VCal_ref["31"]  = 0
        self.VCal_ref["avg"] = 0

        import datetime
        self.startTime = datetime.datetime.now().strftime("%d_%m_%Y_%Hh%M")
        self.subname = "AMC%02d_OH%02d_VFAT2_%d_ID_0x%04x"%(self.slot,self.gtx,self.vfat,self.chipID)
        self.f = open("%s_Data_%s"%(self.startTime,self.subname),'w')
        self.m = open("%s_SCurve_by_channel_%s"%(self.startTime,self.subname),'w')
        self.z = open("%s_Setting_%s"%(self.startTime,self.subname),'w')
        self.h = open("%s_VCal_%s"%(self.startTime,self.subname),'w')
        self.g = open("%s_TRIM_DAC_value_%s"%(self.startTime,self.subname),'w')

        return

    def setupVFAT(self):
        """
        """
        print "------------------------------------------------------"
        print "------------- Testing VFAT2 position %2d--------------"%(self.vfat),
        print "------------------------------------------------------"
        self.z.write("%s-%s\n"%(time.strftime("%Y/%m/%d"),time.strftime("%H:%M:%S")))
        self.z.write("chip ID: 0x%04x\n"%(self.chipID))

        # should make sure all chips are off first?
        writeAllVFATs(self.glib,self.gtx,mask=0xff000000,reg="ContReg0",value=0x0)

        setTriggerSource(self.glib,self.gtx,1)

        biasVFAT(self.glib,self.gtx,self.vfat)
        self.z.write("ipreampin:   168\n")
        self.z.write("ipreampfeed:  80\n")
        self.z.write("ipreampout:  150\n")
        self.z.write("ishaper:     150\n")
        self.z.write("ishaperfeed: 100\n")
        self.z.write("icomp:        75\n")
        self.z.write("vthreshold2:   0\n")
        self.z.write("vthreshold1:   0\n")

        t1_n        = 0
        t1_interval = 400
        t1_delay    = 40

        sendL1ACalPulse(self.glib,self.gtx,t1_delay,t1_interval,t1_n)

        self.z.write("DACs default value: %s\n"%(self.params.DAC_DEF))
        for channel in range(self.params.CHAN_MIN, self.params.CHAN_MAX):
            ## old script had *all* channels set up to receive a pulse at this point, why?
            setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                               mask=0x0,pulse=0x0,trim=self.params.DAC_DEF)
            pass
        return

    def scanThresholdByVFAT(self):
        """
        """
        configureScanModule(self.glib,self.gtx,0,self.vfat,
                            scanmin=0,scanmax=254,stepsize=1,
                            numtrigs=self.params.N_EVENTS_THRESH)
        startScanModule(self.glib,self.gtx)
        data_threshold = getScanResults(self.glib,self.gtx,256)
        return data_threshold

    def scanLatencyByVFAT(self):
        """
        """
        channel = 10
        setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                           mask=0x0,pulse=0x1,trim=self.params.DAC_DEF)
        writeVFAT(self.glib,self.gtx,self.vfat,"VCal",0xff)

        configureScanModule(self.glib,self.gtx,2,self.vfat,
                            scanmin=0,scanmax=254,stepsize=1,
                            numtrigs=self.params.N_EVENTS_LAT)
        startScanModule(self.glib,self.gtx)
        data_latency = getScanResults(self.glib,self.gtx,256)

        setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                           mask=0x0,pulse=0x0,trim=self.params.DAC_DEF)
        writeVFAT(self.glib,self.gtx,self.vfat,"VCal",0x0)
        return data_latency

    def runAllChannels(self):
        """
        """
        # for each channel, disable the cal pulse
        for channel in range(self.params.CHAN_MIN, self.params.CHAN_MAX):
            setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                               mask=0x0,pulse=0x0,trim=self.params.DAC_DEF)
            pass

        for channel in range(self.params.CHAN_MIN, self.params.CHAN_MAX):
            if self.debug:
                if channel > 10:
                    continue
                pass
            print "------------------- channel %3d-------------------"%(channel)
            self.scanChannel(channel)
            pass

        # if self.doQC3:
        #     return

        return

    def scanChannel(self,channel):
        """
        """
        for trim in [0,16,31]:
            print "---------------- s-curve data trimDAC %2d --------------------"%(trim)
            data_scurve = self.scanVCalByVFAT(channel,trim,ntrigs=self.params.N_EVENTS_SCURVE)
            if (trim == 16):
                self.m.write("SCurve_%d\n"%(channel))
                pass
            try:
                for d in data_scurve:
                    Eff = (d & 0xffffff) / (1.*self.params.N_EVENTS_SCURVE)
                    VCal = (d & 0xff000000) >> 24
                    if self.debug:
                        print "%d => %f"%(VCal,Eff)
                        pass
                    if (Eff >= 0.48):
                        print "%d => %f"%(VCal,Eff)
                        self.TotVCal["%s"%(trim)].append(VCal)
                        if (trim == 16):
                            self.m.write("%f\n"%(VCal))
                            self.m.write("%f\n"%(Eff))
                            pass
                        break
                    pass

                # if self.doQC3:
                #     return
            except:
                print "Error while reading the data, they will be ignored"
                pass
            pass

        return

    def scanVCalByVFAT(self,channel,trim,ntrigs):
        """
        """
        setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                           mask=0x0,pulse=0x1,trim=trim)

        configureScanModule(self.glib,self.gtx,3,self.vfat,
                            scanmin=self.params.VCAL_MIN,
                            scanmax=self.params.VCAL_MAX,
                            stepsize=1,
                            numtrigs=ntrigs)
        startScanModule(self.glib,self.gtx)

        data_scurve = getScanResults(self.glib,self.gtx,256)

        setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                           mask=0x0,pulse=0x0,trim=trim)

        return data_scurve

    def adjustTrims(self):
        """
        """
        print
        print "------------------------ TrimDAC routine ------------------------"
        print

        try:
            VCal_ref["0"] = sum(TotVCal["0"])/len(TotVCal["0"])
            self.h.write("%d\n"%(TotVCal0))
            VCal_ref["31"] = sum(TotVCal["31"])/len(TotVCal["31"])
            self.h.write("%d\n"%(TotVCal["31"]))
            VCal_ref["avg"] = (VCal_ref["0"] + VCal_ref["31"])/2
            print "%d VCal_ref[0]   %d"%(VCal_ref["0"])
            print "%d VCal_ref[31]  %d"%(VCal_ref["31"])
            print "%d VCal_ref[avg] %d"%(VCal_ref["avg"])
        except:
            print "S-Curve did not work"
            self.h.close() # changed from self.f.close()
            return False

        for channel in range(self.params.CHAN_MIN, self.params.CHAN_MAX):
            if self.debug:
                if channel > 10:
                    continue
                pass
            self.adjustChannelTrims()
            pass

        self.m.close()
        self.h.write("%d\n"%(TotFoundVCal))
        self.h.close()
        self.g.close()
        # VCalList = [] ## where is this used???
        # minVcal = 0   ## where is this used???

        return True

    def adjustChannelTrims(self,channel):
        """
        """
        TRIM_IT = 0
        print "TrimDAC Channel%d"%(channel)
        trimDAC = 16
        foundGood = False

        while (foundGood == False):
            data_trim = self.scanVCalByVFAT(channel,trimDAC,ntrigs=self.params.N_EVENTS_SCURVE)
            try:
                for d in data_trim:
                    Eff = (d & 0xffffff) / (1.*self.params.N_EVENTS_SCURVE)
                    VCal = (d & 0xff000000) >> 24
                    if (Eff >= 0.48):
                        print "%d => %f"%(VCal,Eff)
                        foundVCal = VCal
                        break
                    pass
                pass
            except:
                print "Error while reading the data, they will be ignored"
                continue

            if (foundVCal > VCal_ref["avg"] and TRIM_IT < self.params.MAX_TRIM_IT and trimDAC < 31):
                trimDAC += 1
                TRIM_IT +=1
            elif (foundVCal < VCal_ref["avg"] and TRIM_IT < self.params.MAX_TRIM_IT and trimDAC > 0):
                trimDAC -= 1
                TRIM_IT +=1
            else:
                self.g.write("%d\n"%(trimDAC))
                self.TotFoundVCal.append(foundVCal)
                self.f.write("S_CURVE_%d\n"%(channel))
                for d in data_trim:
                    self.f.write("%f\n"%((d & 0xff000000) >> 24))
                    self.f.write("%f\n"%((d & 0xffffff)/self.params.N_EVENTS_TRIM))
                    pass
                break
            pass
        return

    def setAllTrims(self):
        """
        """
        self.g = open("%s_TRIM_DAC_value_%s"%(self.startTime,self.subname),'r')
        for channel in range(self.params.CHAN_MIN, self.params.CHAN_MAX):
            if self.debug:
                if channel > 10:
                    continue
                pass
            trimDAC = (self.g.readline()).rstrip('\n')
            print "Setting channel %d trimDAC to %s"%(channel,trimDAC)
            setChannelRegister(self.glib,self.gtx,self.vfat,channel,
                               mask=0x0,pulse=0x0,trim=int(trimDAC))
            pass

        self.g.close()
        return

    ########################## Main routine per VFAT ######################
    def runScanRoutine(self):
        """
        """

        ########################## Setup the VFAT         ######################
        self.setupVFAT()

        ########################## Initial threshold scan ######################
        data_threshold = self.scanThresholdByVFAT()

        print "length of returned data_threshold = %d"%(len(data_threshold))
        for d in range (0,len(data_threshold)):
            noiselevel     = 100*(data_threshold[d  ] & 0xffffff)/(1.*self.params.N_EVENTS_THRESH)
            lastnoiselevel = 100*(data_threshold[d-1] & 0xffffff)/(1.*self.params.N_EVENTS_THRESH)
            print "%d = %f"%(((data_threshold[d] & 0xff000000) >> 24), noiselevel)
            if (noiselevel) < self.params.THRESH_ABS and (lastnoiselevel - noiselevel) < self.params.THRESH_REL:
                setVFATThreshold(self.glib,self.gtx,self.vfat,vt1=(d-1),vt2=0)
                print "Threshold set to: %d"%(d-1)
                self.f.write("Threshold set to: %d\n"%(d-1))
                self.z.write("vthreshold1: %d\n"%(d-1))
                break
            pass
        # self.z.close()

        if d == 0 or d == 255:
            print "ignored"
            for d in range (0,len(data_threshold)):
                self.f.write("%f\n"%((data_threshold[d] & 0xff000000) >> 24))
                self.f.write("%f\n"%(100*(data_threshold[d] & 0xffffff)/(1.*self.params.N_EVENTS_THRESH)))
                pass
            self.f.close()
            return

        for d in range (0,len(data_threshold)):
            self.f.write("%f\n"%((data_threshold[d] & 0xff000000) >> 24))
            self.f.write("%f\n"%(100*(data_threshold[d] & 0xffffff)/(1.*self.params.N_EVENTS_THRESH)))
            pass

        ########################## Initial latency scan ######################
        data_latency = self.scanLatencyByVFAT()

        print "length of returned data_latency = %d"%(len(data_latency))
        for d in range (0,len(data_latency)):
            eff     = 100*(data_latency[d]   & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            lasteff = 100*(data_latency[d-1] & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            nexteff = 100*(data_latency[d+1] & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            print "%d = %f"%(((data_latency[d] & 0xff000000) >> 24), eff)
            if (eff) > self.params.LAT_ABS and (nexteff) > self.params.LAT_ABS and (lasteff) <= self.params.LAT_ABS:
                writeVFAT(self.glib,self.gtx,self.vfat,"Latency",(d+1))
                print "Latency set to: %d"%(d+1)
                self.f.write("Latency set to: %d\n"%(d+1))
                self.z.write("latency: %d\n"%(d+1))
                break
            pass
        self.z.close()

        ################## Run S-Curves on all channels ######################
        self.runAllChannels()

        ################## Adjust the trim for each channel ######################
        if self.adjustTrims():

            ################# Set all the TrimDACs to the right value #################
            self.setAllTrims()
            pass
        
        ########################## Final threshold scan ######################
        self.f.write("second_threshold\n")
        data_threshold = self.scanThresholdByVFAT()
        for d in data_threshold:
            self.f.write("%d\n"%((d & 0xff000000) >> 24))
            self.f.write("%f\n"%(100*(d & 0xffffff)/(1.*self.params.N_EVENTS_THRESH)))
            pass

        ########################## Final latency scan ######################
        data_latency = self.scanLatencyByVFAT()

        print "length of returned data_latency = %d"%(len(data_latency))
        for d in range (0,len(data_latency)):
            eff     = 100*(data_latency[d]   & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            lasteff = 100*(data_latency[d-1] & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            nexteff = 100*(data_latency[d+1] & 0xffffff)/(1.*self.params.N_EVENTS_LAT)
            print "%d = %f"%(((data_latency[d] & 0xff000000) >> 24), eff)
            if (eff) > self.params.LAT_ABS and (nexteff) > self.params.LAT_ABS and (lasteff) <= self.params.LAT_ABS:
                writeVFAT(self.glib,self.gtx,self.vfat,"Latency",(d+1))
                print "Latency set to: %d"%(d+1)
                break
            pass

        self.f.close()

        return



if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      metavar="debug",
                      help="[OPTIONAL] Run in debug mode")
    parser.add_option("-m", "--middle", action="store_true", dest="doMiddle",
                      metavar="doMiddle",
                      help="[OPTIONAL] Use the middle column")
    parser.add_option("-s", "--slot", type="int", dest="slot",
                      help="slot in uTCA crate", metavar="slot", default=10)
    parser.add_option("-g", "--gtx", type="int", dest="gtx",
                      help="GTX on the GLIB", metavar="gtx", default=0)

    parser.add_option("--nglib", type="int", dest="nglib",
                      help="Number of register tests to perform on the glib (default is 100)", metavar="nglib", default=100)
    parser.add_option("--noh", type="int", dest="noh",
                      help="Number of register tests to perform on the OptoHybrid (default is 100)", metavar="noh", default=100)
    parser.add_option("--ni2c", type="int", dest="ni2c",
                      help="Number of I2C tests to perform on the VFAT2s (default is 100)", metavar="ni2c", default=100)
    parser.add_option("--ntrk", type="int", dest="ntrk",
                      help="Number of tracking data packets to readout (default is 100)", metavar="ntrk", default=100)
    parser.add_option("--writeout", action="store_true", dest="writeout",
                      help="Write the data to disk when testing the rate", metavar="writeout")

    parser.add_option("--special", action="store_true", dest="special",
                      metavar="special",
                      help="[OPTIONAL] Run a special arrangement")

    parser.add_option("--QC3test", action="store_true", dest="doQC3",
                      metavar="doQC3",
                      help="[OPTIONAL] Run a shortened test after covers have been applied")

    (options, args) = parser.parse_args()

    sys.path.append('${GEM_PYTHON_PATH}')

    import subprocess,datetime
    startTime = datetime.datetime.now().strftime("%d.%m.%Y-%H.%M.%S.%f")
    print "Start time: %s"%(startTime)

    # Unbuffer output
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    tee = subprocess.Popen(["tee", "%s-log.txt"%(startTime)], stdin=subprocess.PIPE)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    pr.enable()

    from GEMDAQTestSuite import *

    test_params = TEST_PARAMS(nglib=options.nglib,
                              noh=options.noh,
                              ni2c=options.ni2c,
                              ntrk=options.ntrk,
                              writeout=options.writeout)

    scan_params = VFAT_SCAN_PARAMS(
        thresh_abs=0.1,
        thresh_rel=0.05,
        thresh_min=0,
        thresh_max=254,
        lat_abs=0.7,
        lat_min=0,
        lat_max=254,
        nev_thresh=1000,
        nev_lat=3000,
        nev_scurve=1000,
        nev_trim=1000,
        vcal_min=10,
        vcal_max=200,
        max_trim_it=26,
        chan_min=0,
        chan_max=128,
        def_dac=16
        )

    sys.stdout.flush()
    ####################################################

    testsToRun = "A,B,C,D,E,F,G,H"

    print "Running %s on AMC%02d  OH%02d"%(testsToRun,options.slot,options.gtx)

    testSuite = GEMDAQTestSuite(slot=options.slot,
                                gtx=options.gtx,
                                tests=testsToRun,
                                params=test_params,
                                debug=options.debug)

    testSuite.runSelectedTests()

    vfat = 15
    if vfat not in testSuite.presentVFAT2sSingle:
        print "VFAT not found in previous test"
        sys.exit(1)

    sCurveTests = VFATSCurveTools(glib=testSuite.glib,
                                  slot=testSuite.slot,
                                  gtx=testSuite.gtx,
                                  vfat=vfat,
                                  chipID=testSuite.chipIDs[vfat],
                                  params=scan_params,
                                  debug=options.debug)

    print "AMC%02d  OH%02d  VFAT%02d  0x%04x"%(testSuite.slot,testSuite.gtx,vfat,testSuite.chipIDs[vfat])
    print

    sCurveTests.runScanRoutine()

    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print s.getvalue()
