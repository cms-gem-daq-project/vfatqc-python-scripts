'''
@author: Robert Frazier

May 2010
'''

from CommonTools import *
from ChipsException import ChipsException

class AddressTableItem(object):
    '''Represents an address table item for A32/D32 address tables
    
    Note: Addresses, data or masks beyond 32 bits in size will be truncated
    without warning (to the least significant 32-bits of input).  It
    is up to the user of this class to ensure stupid values are not 
    entered.
    '''

    def __init__(self, name, address, mask, read = True, write = True):
        object.__init__(self)
        self._name = name
        self._address = 0xffffffff & address
        self._mask = 0xffffffff & mask
        self._read = bool(read)
        self._write= bool(write)
        self._bitShiftForMaskedData = self._maskedDataBitShift() 

    def getName(self): return self._name
    def getAddress(self): return self._address
    def getMask(self): return self._mask
    def getReadFlag(self): return self._read
    def getWriteFlag(self): return self._write

    def setName(self, name): self._name = name
    def setAddress(self, address): self._address = 0xffffffff & address
    def setMask(self, mask): self._mask = (0xffffffff & mask); self._bitShiftForMaskedData = self._maskedDataBitShift()
    def setReadFlag(self, read): self._read = bool(read)
    def setWriteFlag(self, write): self._write = bool(write)

    def shiftDataToMask(self, data):
        """Shifts data upto the start of the register mask
        
        Note: data over 32-bits in size will be truncated without warning.
        """

        shiftedData = (data & 0xffffffff) << self._bitShiftForMaskedData
        if (~self._mask & shiftedData) != 0:
            raise ChipsException("The data (0x" + uInt32HexStr(data) + ") being written to register '" + 
                                 self._name + "' exceeds bounds of mask!")
        
        return shiftedData
    
    
    def shiftDataFromMask(self, data):
        """Shifts data down from the start register mask"""
        return (data & self._mask) >> self._bitShiftForMaskedData


    def _maskedDataBitShift(self):
        shiftingMask = self._mask
        bitShiftRequired = 0
        while (shiftingMask & 0x1) == 0:
            shiftingMask >>= 1
            bitShiftRequired += 1
        return bitShiftRequired        
