#These are functions which provide the mappings between strips and channels in the V2b electronics
#All directions are in the frame with the narrow end of the detector to the left
# By: Cameron Bravo (c.bravo@cern.ch)
from array import array

def StripToPan(GEBtype,vfat,strip):
    GEBslot = {}
    ROBslot = {}
    for slot in range(0,24):
        ROBslot[slot] = 'left'
        if(GEBtype == 'long' and (slot == 0 or slot == 1 or slot == 16 or slot == 17) ): ROBslot[slot] = 'right'
        if(GEBtype == 'short' and (slot == 0 or slot == 1 or slot == 16 or slot == 17 or slot%8 == 4 or slot%8 == 6) ): ROBslot[slot] = 'right'
        GEBslot[slot] = 'up'
        if(vfat/8 == 2): GEBslot[slot] = 'down'
    panPin = 0
    if(ROBslot[vfat] == 'left'): panPin = (1 - strip/64)*(strip) + (strip/64)*(127 - strip%64)
    else: panPin = (1 - strip/64)*(63 - strip) + (strip/64)*(strip)

    return panPin



