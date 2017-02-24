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

SCAN_THRESH_TRIG=0x0
SCAN_THRESH_CHAN=0x1
SCAN_THRESH_TRK=0x4
SCAN_LATENCY=0x2
SCAN_VCAL=0x3

def txtTitle(str):
    print '\033[1m' + str + '\033[0m'
    return

class VFAT_SCAN_PARAMS:
    """
    """

    def __init__(self,
                 thresh_abs=0.1,thresh_rel=0.05,thresh_min=0,thresh_max=255,
                 lat_abs=90.,lat_min=0,lat_max=255,
                 nev_thresh=3000,nev_lat=3000,
                 nev_scurve=1000,nev_trim=1000,
                 vcal_min=0,vcal_max=255,
                 max_trim_it=26,
                 chan_min=0,chan_max=128,
                 def_dac=16,
                 t1_n=0,t1_interval=300,t1_delay=40
                 ):

        self.THRESH_ABS      = thresh_abs
        self.THRESH_REL      = thresh_rel
        self.THRESH_MIN      = thresh_min
        self.THRESH_MAX      = thresh_max
        self.N_EVENTS_THRESH = nev_thresh

        self.LAT_ABS         = lat_abs
        self.LAT_MIN         = lat_min
        self.LAT_MAX         = lat_max
        self.N_EVENTS_LAT    = nev_lat

        self.VCAL_MIN        = vcal_min
        self.VCAL_MAX        = vcal_max
        self.N_EVENTS_SCURVE = nev_scurve
        self.N_EVENTS_TRIM   = nev_trim
        self.MAX_TRIM_IT     = max_trim_it
        self.CHAN_MIN        = chan_min
        self.CHAN_MAX        = chan_max
        self.DAC_DEF         = def_dac

        self.T1_PARAMS_N        = t1_n
        self.T1_PARAMS_INTERVAL = t1_interval
        self.T1_PARAMS_DELAY     = t1_delay

        return

    def printAll(self):
        print self.THRESH_ABS
        print self.THRESH_REL
        print self.THRESH_MIN
        print self.THRESH_MAX
        print self.N_EVENTS_THRESH
        print
        print self.LAT_ABS
        print self.LAT_MIN
        print self.LAT_MAX
        print self.N_EVENTS_LAT
        print
        print self.VCAL_MIN
        print self.VCAL_MAX
        print self.N_EVENTS_SCURVE
        print self.N_EVENTS_TRIM
        print self.MAX_TRIM_IT
        print self.CHAN_MIN
        print self.CHAN_MAX
        print self.DAC_DEF
        print
        self.T1_PARAMS_N
        self.T1_PARAMS_INTERVAL
        self.T1_PARAMS_DELAY

        return


class VFATSCurveTools:
    """
    This set of tools provides functionality to produce S-Curve results for VFAT2 chips
    @author: Hugo DeWitt
    @modifiedby: Christine McClean
    Jared Sturdy - sturdy@cern.ch (Adapted for uHAL)
    """

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    def __init__(self, glib, slot, gtx, scan_params, doLatency=False,debug=False):
        """
        """
        self.glib   = glib
        self.slot   = slot
        self.gtx    = gtx
        self.scan_params = scan_params
        self.doLatency = doLatency

        self.THRESH_ABS      = scan_params.THRESH_ABS
        self.THRESH_REL      = scan_params.THRESH_REL
        self.THRESH_MIN      = scan_params.THRESH_MIN
        self.THRESH_MAX      = scan_params.THRESH_MAX
        self.LAT_ABS         = scan_params.LAT_ABS
        self.LAT_MIN         = scan_params.LAT_MIN
        self.LAT_MAX         = scan_params.LAT_MAX
        self.N_EVENTS_THRESH = scan_params.N_EVENTS_THRESH
        self.N_EVENTS_LAT    = scan_params.N_EVENTS_LAT
        self.N_EVENTS_SCURVE = scan_params.N_EVENTS_SCURVE
        self.N_EVENTS_TRIM   = scan_params.N_EVENTS_TRIM
        self.VCAL_MIN        = scan_params.VCAL_MIN
        self.VCAL_MAX        = scan_params.VCAL_MAX
        self.MAX_TRIM_IT     = scan_params.MAX_TRIM_IT
        self.CHAN_MIN        = scan_params.CHAN_MIN
        self.CHAN_MAX        = scan_params.CHAN_MAX
        self.DAC_DEF         = scan_params.DAC_DEF
        self.T1_PARAMS_N        = scan_params.T1_PARAMS_N
        self.T1_PARAMS_INTERVAL = scan_params.T1_PARAMS_INTERVAL
        self.T1_PARAMS_DELAY    = scan_params.T1_PARAMS_DELAY

        self.debug  = debug

        self.startTime = None
        self.subname   = None
        self.f = None
        self.m = None
        self.z = None
        self.h = None
        self.g = None

        return

    def cleanup(self,debug=False):
        """
        """
        self.startTime = None
        self.subname   = None
        self.f = None
        self.m = None
        self.z = None
        self.h = None
        self.g = None

        return

    def setupVFAT(self,vfat,debug=False):
        """
        """
        print "------------------------------------------------------"
        print "-------------- Testing VFAT2 position %2d -------------"%(vfat)
        print "------------------------------------------------------"

        if vfat not in range(0,24):
            print "Invalid VFAT specified %d is no in [0,23]"%(vfat)
            sys.exit(-1)
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

        chipID = getChipID(self.glib,self.gtx,vfat)
        self.subname = "AMC_%02d_OH_%02d_VFAT2_%d_ID_0x%04x"%(self.slot,self.gtx,vfat,chipID)

        self.f = open("%s_Data_%s"%(self.startTime,self.subname),'w')
        self.m = open("%s_SCurve_by_channel_%s"%(self.startTime,self.subname),'w')
        self.z = open("%s_Setting_%s"%(self.startTime,self.subname),'w')
        self.h = open("%s_VCal_%s"%(self.startTime,self.subname),'w')
        self.g = open("%s_TRIM_DAC_value_%s"%(self.startTime,self.subname),'w')

        self.m.close()
        self.h.close()
        self.g.close()

        self.z.write("%s-%s\n"%(time.strftime("%Y/%m/%d"),time.strftime("%H:%M:%S")))
        self.z.write("chip ID: 0x%04x\n"%(chipID))

        # should make sure all chips are off first?
        writeAllVFATs(self.glib,self.gtx,reg="ContReg0",value=0x0,mask=0xff000000)

        setTriggerSource(self.glib,self.gtx,1)

        biasVFAT(self.glib,self.gtx,vfat)

        self.z.write("ipreampin:   168\n")
        self.z.write("ipreampfeed:  80\n")
        self.z.write("ipreampout:  150\n")
        self.z.write("ishaper:     150\n")
        self.z.write("ishaperfeed: 100\n")
        self.z.write("icomp:        75\n")
        self.z.write("vthreshold2:   0\n")
        self.z.write("vthreshold1:   0\n")

        print

        sendL1ACalPulse(self.glib,self.gtx,
                        self.T1_PARAMS_DELAY,
                        self.T1_PARAMS_INTERVAL,
                        self.T1_PARAMS_N)
        stopLocalT1(self.glib,self.gtx)

        self.z.write("DACs default value: %s\n"%(self.DAC_DEF))
        for channel in range(self.CHAN_MIN, self.CHAN_MAX):
            ## old script had *all* channels set up to receive a pulse at this point, why?
            setChannelRegister(self.glib,self.gtx,vfat,channel,
                               mask=0x0,pulse=0x0,trim=self.DAC_DEF)
            pass

        return

    def scanThresholdByVFAT(self,vfat,debug=False):
        """
        """

        configureScanModule(self.glib,self.gtx,SCAN_THRESH_TRIG,vfat,
                            scanmin=self.THRESH_MIN,
                            scanmax=self.THRESH_MAX,
                            stepsize=1,numtrigs=self.N_EVENTS_THRESH,
                            debug=debug)
        startScanModule(self.glib,self.gtx)
        if (debug):
            printScanConfiguration(self.glib,self.gtx)
            print "LocalT1Controller status %d"%(getLocalT1Status(self.glib,self.gtx))
            pass
        data_threshold = getScanResults(self.glib,self.gtx,
                                        self.THRESH_MAX - self.THRESH_MIN,
                                        debug=debug)

        return data_threshold

    def scanLatencyByVFAT(self,vfat,debug=False):
        """
        """

        channel = 10
        setChannelRegister(self.glib,self.gtx,vfat,channel,
                           mask=0x0,pulse=0x1,trim=self.DAC_DEF)
        writeVFAT(self.glib,self.gtx,vfat,"VCal",0xff)

        configureScanModule(self.glib,self.gtx,SCAN_LATENCY,vfat,
                            scanmin=self.LAT_MIN,
                            scanmax=self.LAT_MAX,
                            stepsize=1,numtrigs=self.N_EVENTS_LAT,
                            debug=debug)
        startScanModule(self.glib,self.gtx)
        if (debug):
            printScanConfiguration(self.glib,self.gtx)
            print "LocalT1Controller status %d"%(getLocalT1Status(self.glib,self.gtx))
            pass
        data_latency = getScanResults(self.glib,self.gtx,
                                      self.LAT_MAX - self.LAT_MIN,
                                      debug=debug)

        setChannelRegister(self.glib,self.gtx,vfat,channel,
                           mask=0x0,pulse=0x0,trim=self.DAC_DEF)
        writeVFAT(self.glib,self.gtx,vfat,"VCal",0x0)

        return data_latency

    def scanVCalByVFAT(self,vfat,channel,trim,ntrigs,debug=False):
        """
        """

        setChannelRegister(self.glib,self.gtx,vfat,channel,
                           mask=0x0,pulse=0x1,trim=trim)
        if debug:
            print "Channel %d register 0x%08x"%(channel,getChannelRegister(self.glib,self.gtx,vfat,channel))
            pass
        configureScanModule(self.glib,self.gtx,SCAN_VCAL,vfat,
                            channel=channel,
                            scanmin=self.VCAL_MIN,
                            scanmax=self.VCAL_MAX,
                            stepsize=1,numtrigs=ntrigs,
                            debug=debug)
        startScanModule(self.glib,self.gtx)
        if (debug):
            printScanConfiguration(self.glib,self.gtx)
            print "LocalT1Controller status %d"%(getLocalT1Status(self.glib,self.gtx))
            pass
        data_scurve = getScanResults(self.glib,self.gtx,
                                     self.VCAL_MAX - self.VCAL_MIN,
                                     debug=debug)

        setChannelRegister(self.glib,self.gtx,vfat,channel,
                           mask=0x0,pulse=0x0,trim=trim,debug=True)
        if debug:
            print "Channel %d register 0x%08x"%(channel,getChannelRegister(self.glib,self.gtx,vfat,channel))
            pass
        return data_scurve

    def runAllChannels(self,vfat,debug=False):
        """
        """
        # for each channel, disable the cal pulse
        for channel in range(self.CHAN_MIN, self.CHAN_MAX):
            setChannelRegister(self.glib,self.gtx,vfat,channel,
                               mask=0x0,pulse=0x0,trim=self.DAC_DEF)
            pass

        for channel in range(self.CHAN_MIN, self.CHAN_MAX):
            if self.debug and (channel > 10):
                continue
            self.scanChannel(vfat,channel,debug=debug)
            pass

        return

    def scanChannel(self,vfat,channel,debug=False):
        """
        """
        print "--------------------- Channel %03d ---------------------------"%(channel)

        self.m = open("%s_SCurve_by_channel_%s"%(self.startTime,self.subname),'a')
        for trim in [0,16,31]:
            print "---------------- S-Curve data trimDAC %2d --------------------"%(trim)
            data_scurve = self.scanVCalByVFAT(vfat,channel,trim,ntrigs=self.N_EVENTS_SCURVE,debug=debug)
            if (trim == 16):
                self.m.write("SCurve_%d\n"%(channel))
                pass
            try:
                if debug:
                    print "Length of returned data_scurve = %d"%(len(data_scurve))
                    print "First data word: 0x%08x"%(data_scurve[0])
                    for d in range (0,len(data_scurve)):
                        "%d ==> %3.4f"%((data_scurve[d] & 0xff000000) >> 24,
                                        (data_scurve[d] & 0xffffff) / (1.*self.N_EVENTS_SCURVE))
                        pass
                    pass
                passed = False
                for d in data_scurve:
                    VCal = (d & 0xff000000) >> 24
                    Eff  = (d & 0xffffff) / (1.*self.N_EVENTS_SCURVE)
                    if self.debug:
                        print "%d => %3.4f"%(VCal,Eff)
                        pass
                    if (Eff >= 0.48 and not passed):
                        if not passed:
                            print "%d => %3.4f"%(VCal,Eff)
                            self.TotVCal["%s"%(trim)].append(VCal)
                            pass
                        passed = True
                        if trim in [0,31]:
                            break # stop scanning for high and low trim values
                        pass
                    if (trim == 16):
                        self.m.write("%d\t%f\n"%(VCal,Eff))  # write to file for trim == 16
                        pass
                    pass

                # if self.doQC3:
                #     return
            except:
                ex = sys.exc_info()[0]
                print "Caught exception: %s"%(ex)
                print "Error while reading the data, they will be ignored"
                self.m.close()
                pass
            pass
        self.m.close()
        return

    def adjustTrims(self,vfat,debug=False):
        """
        """
        print
        print "------------------------ TrimDAC routine ------------------------"
        print

        self.h = open("%s_VCal_%s"%(self.startTime,self.subname),'a')
        if debug:
            for trim in [0,16,31]:
                print "TotVCal[%d](length = %d) = %s"%(trim,
                                                       len(self.TotVCal["%d"%(trim)]),
                                                       self.TotVCal["%d"%(trim)])
                pass
            pass

        try:
            self.VCal_ref["0"]  = sum(self.TotVCal["0"])/len(self.TotVCal["0"])
            print "VCal_ref[0]   %d"%(self.VCal_ref["0"])
            self.VCal_ref["31"] = sum(self.TotVCal["31"])/len(self.TotVCal["31"])
            print "VCal_ref[31]  %d"%(self.VCal_ref["31"])
            self.VCal_ref["avg"] = (self.VCal_ref["0"] + self.VCal_ref["31"])/2
            print "VCal_ref[avg] %d"%(self.VCal_ref["avg"])
            self.h.write("%s\n"%(self.TotVCal["0"]))
            self.h.write("%s\n"%(self.TotVCal["31"]))
        except:
            ex = sys.exc_info()[0]
            print "Caught exception: %s"%(ex)
            print "S-Curve did not work"
            self.h.close() # changed from self.f.close()
            return False

        self.g = open("%s_TRIM_DAC_value_%s"%(self.startTime,self.subname),'a')
        for channel in range(self.CHAN_MIN, self.CHAN_MAX):
            if self.debug and (channel > 10):
                continue
            self.adjustChannelTrims(vfat,channel,debug)
            pass

        self.h.write("%s\n"%(self.TotFoundVCal))
        # VCalList = [] ## where is this used???
        # minVcal = 0   ## where is this used???

        self.h.close()
        self.g.close()

        return True

    def adjustChannelTrims(self,vfat,channel,debug=False):
        """
        """
        TRIM_IT = 0
        print "TrimDAC Channel%d"%(channel)
        trimDAC = 16
        foundGood = False

        foundVCal = None # this was not properly scoped previosly, where do we want to initialize it?
        while (foundGood == False):
            data_trim = self.scanVCalByVFAT(vfat,channel,trimDAC,ntrigs=self.N_EVENTS_SCURVE,debug=debug)
            if debug:
                print "First data word: 0x%08x"%(data_trim[0])
                pass
            try:
                for d in data_trim:
                    VCal = (d & 0xff000000) >> 24
                    Eff  = (d & 0xffffff) / (1.*self.N_EVENTS_SCURVE)
                    if (Eff >= 0.48):
                        print "%d => %3.4f"%(VCal,Eff)
                        foundVCal = VCal
                        break
                    pass
                pass
            except:
                ex = sys.exc_info()[0]
                print "Caught exception: %s"%(ex)
                print "Error while reading the data, they will be ignored"
                continue

            if (foundVCal > self.VCal_ref["avg"] and TRIM_IT < self.MAX_TRIM_IT and trimDAC < 31):
                trimDAC += 1
                TRIM_IT +=1
            elif (foundVCal < self.VCal_ref["avg"] and TRIM_IT < self.MAX_TRIM_IT and trimDAC > 0):
                trimDAC -= 1
                TRIM_IT +=1
            else:
                self.g.write("%d\n"%(trimDAC))
                self.TotFoundVCal.append(foundVCal)
                self.f.write("S_CURVE_%d\n"%(channel))
                for d in data_trim:
                    self.f.write("%d\t%f\n"%((d & 0xff000000) >> 24,(d & 0xffffff)/(1.*self.N_EVENTS_TRIM)))
                    pass
                break
            pass
        return

    def setAllTrims(self,vfat,debug=False):
        """
        """

        self.g = open("%s_TRIM_DAC_value_%s"%(self.startTime,self.subname),'r')
        for channel in range(self.CHAN_MIN, self.CHAN_MAX):
            if self.debug and (channel > 10):
                continue
            trimDAC = (self.g.readline()).rstrip('\n')
            print "Setting channel %d trimDAC to %s"%(channel,trimDAC)
            setChannelRegister(self.glib,self.gtx,vfat,channel,
                               mask=0x0,pulse=0x0,trim=int(trimDAC))
            pass
        self.g.close()
        return

    ########################## Main routine per VFAT ######################
    def runScanRoutine(self,vfat,debug=False):
        """
        """
        chipID = getChipID(self.glib,self.gtx,vfat)
        print "AMC%02d  OH%02d  VFAT%02d  0x%04x"%(self.slot,self.gtx,vfat,chipID)
        print
        ########################## Setup the VFAT         ######################
        print "Setup the VFAT"
        self.setupVFAT(vfat)

        ########################## Initial threshold scan ######################
        print "Initial threshold scan"
        data_threshold = self.scanThresholdByVFAT(vfat,debug=debug)
        print "Length of returned data_threshold = %d"%(len(data_threshold))
        threshold = 0
        noise = 100*(data_threshold[0] & 0xffffff)/(1.*self.N_EVENTS_THRESH)
        if debug:
            print "First data word: 0x%08x"%(data_threshold[0])
            pass
        print "%d = %3.4f"%(((data_threshold[0] & 0xff000000) >> 24), noise)
        for d in range (1,len(data_threshold)-1):
            noise     = 100*(data_threshold[d  ] & 0xffffff)/(1.*self.N_EVENTS_THRESH)
            lastnoise = 100*(data_threshold[d-1] & 0xffffff)/(1.*self.N_EVENTS_THRESH)
            nextnoise = 100*(data_threshold[d+1] & 0xffffff)/(1.*self.N_EVENTS_THRESH)

            passAbs     = (noise) < self.THRESH_ABS
            passLastRel = (lastnoise - noise) < self.THRESH_REL
            passNextRel = abs(noise - nextnoise) < self.THRESH_REL

            print "%d = %3.4f"%(((data_threshold[d] & 0xff000000) >> 24), noise)
            if passAbs and passLastRel and passNextRel:
                # why is the threshold set to the previous value?
                threshold = (data_threshold[d] >> 24 )
                setVFATThreshold(self.glib,self.gtx,vfat,vt1=(threshold),vt2=0)
                print "Threshold set to: %d"%(threshold)
                self.f.write("Threshold set to: %d\n"%(threshold))
                self.z.write("vthreshold1: %d\n"%(threshold))
                break
            pass
        # self.z.close()

        if threshold == 0 or threshold == 255:
            print "ignored"
            for d in range (0,len(data_threshold)):
                self.f.write("%d\t%f\n"%((data_threshold[d] & 0xff000000) >> 24,
                                         100*(data_threshold[d] & 0xffffff)/(1.*self.N_EVENTS_THRESH)))
                pass
            self.f.close()
            return

        for d in range (0,len(data_threshold)):
            self.f.write("%d\t%f\n"%((data_threshold[d] & 0xff000000) >> 24,
                                     100*(data_threshold[d] & 0xffffff)/(1.*self.N_EVENTS_THRESH)))
            pass

        ##################Parts of the routine require the L1A+CalPulse ######################
        startLocalT1(self.glib,self.gtx)

        ########################## Initial latency scan ######################
        if self.doLatency:
            print "Initial latency scan"

            data_latency = self.scanLatencyByVFAT(vfat,debug=debug)

            print "Length of returned data_latency = %d"%(len(data_latency))
            if not len(data_latency):
                print "data_latency is empty"
                return
            if debug:
                print "First data word: 0x%08x"%(data_latency[0])
                pass
            eff     = 100*(data_latency[0]   & 0xffffff)/(1.*self.N_EVENTS_LAT)
            print "%d = %3.4f"%(((data_latency[0] & 0xff000000) >> 24), eff)
            for d in range (1,len(data_latency)-1):
                eff     = 100*(data_latency[d]   & 0xffffff)/(1.*self.N_EVENTS_LAT)
                lasteff = 100*(data_latency[d-1] & 0xffffff)/(1.*self.N_EVENTS_LAT)
                nexteff = 100*(data_latency[d+1] & 0xffffff)/(1.*self.N_EVENTS_LAT)
                print "%d = %3.4f"%(((data_latency[d] & 0xff000000) >> 24), eff)
                if (eff) > self.LAT_ABS and (nexteff) > self.LAT_ABS and (lasteff) <= self.LAT_ABS:
                    latency = (data_latency[d+1] >> 24 )
                    writeVFAT(self.glib,self.gtx,vfat,"Latency",(latency))
                    print "Latency set to: %d"%(latency)
                    self.f.write("Latency set to: %d\n"%(latency))
                    self.z.write("latency: %d\n"%(latency))
                    #if not debug:
                    break
                    #pass
                pass
            pass
        else:
            writeVFAT(self.glib,self.gtx,vfat,"Latency",(37))
            print "Latency set to: %d"%(37)
            self.f.write("Latency set to: %d\n"%(37))
            self.z.write("latency: %d\n"%(37))
            pass
        self.z.close()

        ################## Run S-Curves on all channels ######################
        print "Run S-Curves on all channels"
        self.runAllChannels(vfat,debug=debug)

        # if self.doQC3:
        #     return

        ################## Adjust the trim for each channel ######################
        print "Adjust the trim for each channel"
        if self.adjustTrims(vfat,debug=debug):

            ################# Set all the TrimDACs to the right value #################
            print "Set all the TrimDACs to the right value"
            self.setAllTrims(vfat,debug=debug)
            pass

        ########################## Final threshold scan ######################
        print "Final threshold scan"
        stopLocalT1(self.glib,self.gtx)
        self.f.write("second_threshold\n")
        data_threshold = self.scanThresholdByVFAT(vfat,debug=debug)
        if not len(data_threshold):
            print "data_threshold is empty"
            return
        if debug:
            print "First data word: 0x%08x"%(data_threshold[0])
            pass
        for d in data_threshold:
            self.f.write("%d\t%f\n"%((d & 0xff000000) >> 24,
                                     100*(d & 0xffffff)/(1.*self.N_EVENTS_THRESH)))
            pass

        ########################## Final latency scan ######################
        if self.doLatency:
            print "Final latency scan"
            startLocalT1(self.glib,self.gtx)
            data_latency = self.scanLatencyByVFAT(vfat,debug=debug)

            print "Length of returned data_latency = %d"%(len(data_latency))
            if not len(data_latency):
                print "data_latency is empty"
                return
            if debug:
                print "First data word: 0x%08x"%(data_latency[0])
                pass
            eff     = 100*(data_latency[0]   & 0xffffff)/(1.*self.N_EVENTS_LAT)
            print "%d = %3.4f"%(((data_latency[0] & 0xff000000) >> 24), eff)
            for d in range (1,len(data_latency)-1):
                eff     = 100*(data_latency[d]   & 0xffffff)/(1.*self.N_EVENTS_LAT)
                lasteff = 100*(data_latency[d-1] & 0xffffff)/(1.*self.N_EVENTS_LAT)
                nexteff = 100*(data_latency[d+1] & 0xffffff)/(1.*self.N_EVENTS_LAT)
                print "%d = %3.4f"%(((data_latency[d] & 0xff000000) >> 24), eff)
                if (eff) > self.LAT_ABS and (nexteff) > self.LAT_ABS and (lasteff) <= self.LAT_ABS:
                    writeVFAT(self.glib,self.gtx,vfat,"Latency",(d+1))
                    print "Latency set to: %d"%(d+1)
                    break
                pass
            pass
        else:
            pass

        self.f.close()
        self.cleanup()

        if debug:
            raw_input("enter to finish")
            pass
        ##################### Stop local T1 controller ######################
        resetLocalT1(self.glib,self.gtx)

        return


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      metavar="debug",
                      help="[OPTIONAL] Run in debug mode")
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

    parser.add_option("--doLatency", action="store_true", dest="doLatency",
                      metavar="doLatency",
                      help="[OPTIONAL] Run latency scan to determine the latency value")

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

    # import cProfile, pstats, StringIO
    # pr = cProfile.Profile()
    # pr.enable()

    from GEMDAQTestSuite import *

    test_params = TEST_PARAMS(nglib=options.nglib,
                              noh=options.noh,
                              ni2c=options.ni2c,
                              ntrk=options.ntrk,
                              writeout=options.writeout)

    scan_params = VFAT_SCAN_PARAMS(
        thresh_abs=0.15,
        thresh_rel=0.05,
        thresh_min=0,
        thresh_max=255,
        lat_abs=98.,
        lat_min=0,
        lat_max=255,
        nev_thresh=100000,
        nev_lat=1000,
        nev_scurve=250,
        nev_trim=250,
        vcal_min=0,
        vcal_max=255,
        max_trim_it=26,
        chan_min=0,
        chan_max=128,
        def_dac=16,
        t1_n=0,
        t1_interval=150,
        t1_delay=10
        )

    sys.stdout.flush()
    ####################################################

    testsToRun = "A,B,C,D,E,F"

    print "Running %s on AMC%02d  OH%02d"%(testsToRun,options.slot,options.gtx)

    testSuite = GEMDAQTestSuite(slot=options.slot,
                                gtx=options.gtx,
                                tests=testsToRun,
                                test_params=test_params)#,
                                #debug=options.debug)

    testSuite.runSelectedTests()

    vfat = 0
    if vfat not in testSuite.presentVFAT2sSingle:
        print "VFAT not found in previous test"
        sys.exit(1)

    sCurveTests = VFATSCurveTools(glib=testSuite.glib,
                                  slot=testSuite.slot,
                                  gtx=testSuite.gtx,
                                  scan_params=scan_params,
                                  doLatency=options.doLatency,
                                  debug=options.debug)

    sCurveTests.runScanRoutine(vfat,options.debug)

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'cumulative'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print s.getvalue()
