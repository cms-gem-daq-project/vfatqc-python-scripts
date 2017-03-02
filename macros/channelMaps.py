#These are functions which provide the mappings between strips and channels in the V2b electronics
#All directions are in the frame with the narrow end of the detector to the left
# By: Cameron Bravo (c.bravo@cern.ch)
from array import array

def stripToChannel(GEBtype,vfat,strip):
    GEBslot = {}
    ROBslot = {}
    for slot in range(0,24):
        ROBslot[slot] = 'left'
        if(GEBtype == 'long' and (slot == 0 or slot == 1 or slot == 16 or slot == 17) ): ROBslot[slot] = 'right'
        if(GEBtype == 'short' and (slot == 0 or slot == 1 or slot == 16 or slot == 17 or slot%8 == 4 or slot%8 == 6) ): ROBslot[slot] = 'right'
        GEBslot[slot] = 'up'
        if(vfat/8 == 2): GEBslot[slot] = 'down'
    panPin = 0
    if(ROBslot[vfat] == 'left'): panPin = (1 - strip/64)*(63 - strip) + (strip/64)*(strip)
    if(ROBslot[vfat] == 'right'): panPin = (1 - strip/64)*(strip) + (strip/64)*(127 - strip%64)

    panPinToChannel = array('l',[1,3,5,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,31,29,27,25,23,21,84,86,88,90,92,94,96,98,100,102,104,106,108,110,45,43,41,39,37,35,33,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,59,63,7,9,11,13,15,17,19,82,80,78,76,74,72,70,68,66,65,67,69,71,73,75,77,79,81,83,85,87,89,91,93,95,97,99,101,103,105,107,109,111,113,115,117,119,121,123,125,127,128,126,124,122,120,118,116,114,112,47,49,51,53,55,57,61])
    channel = 0
    if(GEBslot[vfat] == 'down'): channel = panPinToChannel[panPin] - 1
    else: channel = panPinToChannel[127 - panPin] - 1

    return channel

def channelToStrip(vfat,channel):
    strip = -1
    for i in range(0,127):
        if(stripToChannel(vfat,i) == channel): strip = i

    return strip
