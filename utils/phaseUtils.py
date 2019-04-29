def crange(start,stop,modulus):
    """crange returns a list of the elements in the appropriate range
    x,y where x < y, y < 2*modulo: [ x, x+1 ,,, modulus-1 , 0, ,,, y%modulus ]
    x,y where x > y [ x, x+1 ,,, modulo-1 , 0, ,,, y ]
    all other cases are invalid
    """
    
    if start < stop:
        return [ x % modulus for x in range(start,stop) ]
    elif stop < start:
        return [ x for x in range(start,modulus) ] + [ x for x in range(0,stop) ]
    else:
        # return []
        raise IndexError("Invalid range specified")

def getSequentialBadPhases(badPhaseCounts):
    """
    Returns a tuple containing:

        (true/false, minSeqPhase, maxSeqPhase, idx2Use)

    Where the first element is true (false) if squential bad phases (do not) exist.
    The last element idx2Use contains a list of nonsequential bad phases

    badPhaseCounts - container whose elements indicate bad GBT phase positions 
    """

    badPhasesAreSequential=False
    minSeqPhase = -1
    maxSeqPhase = -1
    nBadPhases = len(badPhaseCounts)

    idx2Use = [ x for x in range(0,nBadPhases) ]
    
    for idx1 in range(0,nBadPhases):
        for idx2 in range(0,nBadPhases):
            if not (idx1 > idx2):
                continue
            if( int(abs(badPhaseCounts[idx1]-badPhaseCounts[idx2])) == 1): #bad phases are sequential
                minSeqPhase = int(min(badPhaseCounts[idx1],badPhaseCounts[idx2]))
                maxSeqPhase = int(max(badPhaseCounts[idx1],badPhaseCounts[idx2]))
                idx2Use.remove(idx1)
                idx2Use.remove(idx2)
                badPhasesAreSequential=True
                break # exit inner loop
            pass
        if (badPhasesAreSequential):
            break # exit outer loop
        pass

    return (badPhasesAreSequential, minSeqPhase, maxSeqPhase, idx2Use)

def getPhaseFromLongestGoodWindow(badPhase, phaseCounts):
    """
    If there is only one bad phase, given by badPhase, in a phase scan this will
    look for the longest good window and return a good phase value from that

    badPhase    - the phase in the phase scan that is bad
    phaseCounts - numpy array holding results of a phase scan
    """
    # only one bad phase point, search forward and backwards for most "good" phases
    # wraparound needs to be handled by a circular range function
    # phase == 15 needs to be handled, currently included in the sum
    from gempython.tools.hw_constants import GBT_PHASE_RANGE 
    WINDOW = 4
    frange  = crange(int(badPhase+1),
                     int(badPhase)+1+WINDOW,
                     GBT_PHASE_RANGE)
    brange  = crange(int(badPhase)-WINDOW,
                     int(badPhase),
                     GBT_PHASE_RANGE)
    fsum = sum(phaseCounts.take(frange, mode='wrap')) # forward  sum
    bsum = sum(phaseCounts.take(brange, mode='wrap')) # backward sum
    if fsum > bsum:
        return int((badPhase+WINDOW)%GBT_PHASE_RANGE)
    elif bsum > fsum:
        return int((badPhase-WINDOW)%GBT_PHASE_RANGE)
    else:
        ## choose the phase that doesn't require passing 15?
        return int((badPhase-WINDOW)%GBT_PHASE_RANGE)

def phaseIsGood(vfatBoard,vfat,phase):
    """
    Writes GBT phase to value 'phase' for given vfat
    Returns true if this phrase is good

    vfatBoard - Instance of HwVFAT class
    vfat      - Number indicating vfat position in range [0,23]
    phase     - Phase value to write in range [0,15]
    """
    
    # Get hardware info
    cardName = vfatBoard.parentOH.parentAMC.name
    ohN      = vfatBoard.parentOH.link
    phase    = vfatBoard.parentOH.vfatGBTPhases[vfat]

    # Set GBT phase
    from xhal.reg_interface_gem.core.gbt_utils_extended import setPhase
    setPhase(cardName,ohN,vfat,phase)
    
    # Issue link reset
    vfatBoard.parentOH.parentAMC.writeRegister("GEM_AMC.GEM_SYSTEM.CTRL.LINK_RESET",0x1)

    # Check slow control with this VFAT
    from xhal.reg_interface_gem.core.reg_extra_ops import repeatedRead
    readErrors  = repeatedRead("GEM_AMC.OH.OH{0}.GEB.VFAT{1}.CFG_RUN".format(ohN,vfat),1000,True)
    readErrors += repeatedRead("GEM_AMC.OH.OH{0}.GEB.VFAT{1}.HW_ID".format(ohN,vfat),1000,True)
    readErrors += repeatedRead("GEM_AMC.OH.OH{0}.GEB.VFAT{1}.HW_ID_VER".format(ohN,vfat),1000,True)

    return (readErrors == 0)
