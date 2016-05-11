'''
Created on May 17, 2010

@author: Robert Frazier
'''

from array import array
import IPbusHeader
from ChipsException import ChipsException
from CommonTools import uInt32HexStr


class TransactionElement(object):
    '''Represents a single IPbus request or response (read, write, etc.).'''


    def __init__(self, arrayU32):
        '''Construct from a unsigned 32-bit array object'''
        object.__init__(self)
        if isinstance(arrayU32, array) and arrayU32.typecode == 'I' and len(arrayU32) >= 1:
            # self._rawData holds header and body, to make serialisation as fast as possible
            self._rawData = arrayU32
        else:
            raise ChipsException("Cannot construct a TransactionElement object from anything other " \
                                 "than an unsigned 32-bit array object of length >= 1!")

    @classmethod
    def makeFromHeaderAndBody(cls, headerU32, bodyU32List = []):
        '''Construct a TransactionElement object from a header and an optional body list.
        
        header:  A raw unsigned 32-bit header word.
        bodyU32List:  A list of unsigned 32-bit words (optional).
        '''
        arrayU32 = array('I', [headerU32] + bodyU32List)
        return cls(arrayU32)


    def getAll(self):
        '''Returns the all the raw data of the transaction element (i.e. header & body)
        
        Returns an array object with TypeCode = 'I' (i.e. unsigned 32-bit array).
        '''
        return self._rawData


    def getU32TransmitSize(self):
        '''Returns the transmit size of the TransactionElement in terms of number of 32-bit words'''
        return len(self._rawData)


    def getHeader(self):
        '''Return the 32-bit header word of the TransactionElement.
        
        Use the helper functions in the IPbusHeader module if you want to decode the returned header.
        '''
        return self._rawData[0]


    def getBody(self):
        '''Get the body of the TransactionElement.
        
        Returns an array object with TypeCode = 'L' (i.e. unsigned 32-bit array).
        '''
        return self._rawData[1:]


    def validBodySize(self):
        '''Returns true/false if the current body size matches the size inferred by the header.'''
        return (len(self._rawData) - 1) == IPbusHeader.getExpectedBodySize(self.getHeader())

    
    def __repr__(self):
        '''For representing the object in string form'''
        resultString = "  0x" + uInt32HexStr(self.getHeader()) + "\tHeader\n"
        for index, u32 in enumerate(self.getBody()):
            resultString += "  0x" + uInt32HexStr(u32) + "\tBody " + str(index) + "\n"
        return resultString



def reprTransactionElementList(transactionElementList):
    """Convenience function for getting a string representation of a list of transaction elements"""
    resultString = ""
    for element in transactionElementList:
        resultString += repr(element)
    return resultString


