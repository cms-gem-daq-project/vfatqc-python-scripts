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
    if(ROBslot[vfat] == 'left'): panPin = (1 - strip/64)*(strip) + (strip/64)*(127 - strip%64)
    else: panPin = (1 - strip/64)*(63 - strip) + (strip/64)*(strip)

    panPinToChannel = array('l',[124,116,112,108,104,100,96,93,97,101,105,109,113,117,121,125,127,123,119,115,111,107,103,99,95,91,87,83,79,75,71,67,63,59,55,51,47,43,39,35,31,27,23,19,15,11,7,3,1,5,9,13,17,21,25,29,33,40,36,32,28,24,20,16,128,120,126,122,118,114,110,106,102,98,94,90,86,82,78,74,70,66,68,72,76,80,84,88,92,89,85,81,77,73,69,65,61,57,53,49,45,41,37,44,48,52,56,60,64,62,58,54,50,46,42,38,34,30,26,22,18,14,10,6,2,12,8,4])
    #This is from a schematic I got from Andrew, the other is from Misha panPinToChannel = array('l',[1,3,5,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,31,29,27,25,23,21,84,86,88,90,92,94,96,98,100,102,104,106,108,110,45,43,41,39,37,35,33,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,59,63,7,9,11,13,15,17,19,82,80,78,76,74,72,70,68,66,65,67,69,71,73,75,77,79,81,83,85,87,89,91,93,95,97,99,101,103,105,107,109,111,113,115,117,119,121,123,125,127,128,126,124,122,120,118,116,114,112,47,49,51,53,55,57,61])
    channel = 0
    if(GEBslot[vfat] == 'up'): channel = panPinToChannel[panPin] - 1
    else: channel = panPinToChannel[127 - panPin] - 1

    return channel

def channelToStrip(GEBtype,vfat,channel):
    strip = -1
    for i in range(0,127):
        if(stripToChannel(GEBtype,vfat,i) == channel): strip = i

    return strip


