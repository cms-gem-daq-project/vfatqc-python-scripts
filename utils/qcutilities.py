def calcL1Ainterval(rate):
    """
    Returns the L1Ainterval in BX associated with a given rate in Hz
    """
    from math import floor
    return floor((1.0 / rate) * (1e9 / 25))

def getCardName(shelf,slot):
    return "gem-shelf%02d-amc%02d"%(shelf,slot)

def getGeoInfoFromCardName(cardName):
    """
    cardName is expected to be of the form 'gem-shelfXX-amcYY' where XX & YY are integers
    """
    shelf = getShelfFromCardName(cardName)
    slot = getSlotFromCardName(cardName)
    return {"shelf":shelf,"slot":slot}

def getShelfFromCardName(cardName):
    """
    cardName is expected to be of the form 'gem-shelfXX-amcYY' where XX & YY are integers
    """
    shelf = (split(cardName,"-")[1])
    shelf = int(shelf.strip("shelf"))
    return shelf

def getSlotFromCardName(cardName):
    """
    cardName is expected to be of the form 'gem-shelfXX-amcYY' where XX & YY are integers
    """
    shelf = (split(cardName,"-")[2])
    shelf = int(shelf.strip("amc"))
    return shelf

def inputOptionsValid(options, amc_major_fw_ver):
    """
    Sanity check on input options

    options - Either an optparser.Values instance or a dictionary
    amc_major_fw_ver - major FW version of the AMC
    """

    # get the options dictionary
    if type(options) == type({}):
        dict_options = options
    else:
        dict_options = options.__dict__.keys()

    # Cal Phase
    if "CalPhase" in dict_options:
        if amc_major_fw_ver < 3:
            if options.CalPhase < 0 or options.CalPhase > 8:
                print 'CalPhase must be in the range 0-8'
                return False
            pass
        else:
            if options.CalPhase < 0 or options.CalPhase > 7:
                print 'CalPhase must be in the range 0-7'
                return False
            pass
        pass
    
    # CFG_CAL_SF
    if "calSF" in dict_options and amc_major_fw_ver >= 3: # V3 Behavior only
        if options.calSF < 0 or options.calSF > 3:
            print 'calSF must be in the range 0-3'
            return False
        pass
    
    # Channel Range
    if (("chMin" in dict_options) and ("chMax" in dict_options)):
        if not (0 <= options.chMin <= options.chMax < 128):
            print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
            return False
        pass

    # MSPL or Pulse Stretch
    if "MSPL" in dict_options:
        if amc_major_fw_ver < 3:
            if options.MSPL not in range(1,9):
                print("Invalid MSPL specified: %d, must be in range [1,8]"%(options.MSPL))
                return False
            pass
        else:
            if options.MSPL not in range(0,8):
                print("Invalid MSPL specified: %d, must be in range [0,7]"%(options.MSPL))
                return False
            pass
        pass

    # step size
    if "stepSize" in dict_options:
        if options.stepSize <= 0:
            print("Invalid stepSize specified: %d, must be in range [1, %d]"%(options.stepSize, options.scanmax-options.scanmin))
            return False
        pass

    # VThreshold2
    if ( ("vt2" in dict_options) and (amc_major_fw_ver < 3)): # Only v2b behavior
        if options.vt2 not in range(256):
            print("Invalid VT2 specified: %d, must be in range [0,255]"%(options.vt2))
            return False
        pass

    # Input options are valid
    return True
