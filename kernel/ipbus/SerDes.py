'''
Created on June 22, 2011

@author: Robert Frazier
'''

from array import array
from IPbusHeader import getExpectedBodySize
from TransactionElement import TransactionElement, reprTransactionElementList
from CommonTools import uInt32HexStr
import logging
from ChipsLog import chipsLog
from ChipsException import ChipsException


class SerDes(object):
    '''Class for serialising/deserialising IPbus transaction data
    
    Can serialise a list of TransactionElements into a string, or deserialise
    a string into a list of TransactionElements.  The deserialisation stage
    checks the byte-ordering by looking for a byte-order header, and deals
    with the byte-reordering as appropriate.  If a byte-reorder was required
    on the deserialisation stage, then the serialisation stage will also
    perform a reorder in order to respond correctly.
    
    Byte-reordering is off by default, as it's obviously a waste of CPU.
    '''


    def __init__(self):
        '''Constructor - no arguments'''
        object.__init__(self)
        self._doByteReorder = False;
    
    
    def serialise(self, transactionElementList):
        '''Serialises a list of transaction elements into an ASCII string for transmission'''
    
        if chipsLog.level <= logging.DEBUG:
            msg = "\nSerialising the following packet content:\n"
            msg += reprTransactionElementList(transactionElementList)
            chipsLog.debug(msg)
    
        allTransactionsArray = array('I', [0x200000f0])   # TEMPORARY IPBUS V2.x HACK!   Add a packet header of [0x200000f0] to the beginning of each packet.
        extendFunc = allTransactionsArray.extend
        for element in transactionElementList:
            extendFunc(element.getAll())
        if self._doByteReorder: allTransactionsArray.byteswap()
        return allTransactionsArray.tostring()
    
    
    def deserialise(self, packetPayloadString):
        '''Deserialises a packet payload ASCII string into list of transaction elements'''
    
        # 1) Unpack the string into unsigned integers
        try:
            rawU32Array = array('I', packetPayloadString)  # Unpack string to an unsigned 32-bit array
        except Exception, err:
            raise ChipsException("Deserialisation error:\n\t" + str(err))
    
        # 2) Debug output of the raw packet
        if chipsLog.level <= logging.DEBUG:
            msg = "\nRaw received packet content is:\n"
            for u32 in rawU32Array: msg += "  0x" + uInt32HexStr(u32) + "\n"
            chipsLog.debug(msg)
    
        # 3) Detect if we need to do a byte-reorder
        firstWord = rawU32Array[0]
        firstWordMasked = firstWord & 0xf00000f0  # This selects only the bits relevant for detecting the byte ordering
        if firstWordMasked == 0x200000f0:
            chipsLog.debug("Packet header detected: no byte-reorder is required.")
        elif firstWordMasked == 0xf0000020:
            chipsLog.debug("Packet header detected: a byte-reorder will be performed.")
            self._doByteReorder = True
        else:
            chipsLog.warn("Warning: No packet header (or unknown protocol version)! First word = 0x" + uInt32HexStr(firstWord) + ". Will hope for the best!...")
        
        # 4) Do the byte-reorder if necessary
        if self._doByteReorder:  rawU32Array.byteswap()
       
        # 5) Now deserialise into a list of TransactionElements
        transactionElementList = []  # The list all the deserialised transaction elements will go into
        appendToTransactionElementList = transactionElementList.append  # This is needed for a speed optimisation
        iU32 = 1  # Index for moving through the rawU32Array          # TEMPORARY IPBUS V2.x HACK! Skip the first word which is now a packet ID
        rawU32ArraySize = len(rawU32Array)
        while iU32 < rawU32ArraySize:
            expectedBodySize = getExpectedBodySize(rawU32Array[iU32])
            if rawU32ArraySize - iU32 - 1 - expectedBodySize < 0:
                raise ChipsException("Deserialisation error: packet not correctly formatted " \
                                     "or does not contain the expected amount of data!")
            appendToTransactionElementList(TransactionElement(rawU32Array[iU32: iU32 + 1 + expectedBodySize]))
            iU32 += (1 + expectedBodySize)
        
        # 6) Debug output of deserialised packet content
        if chipsLog.level <= logging.DEBUG:
            msg = "\nDeserialised packet content is:\n" \
                  + reprTransactionElementList(transactionElementList)
            chipsLog.debug(msg)
            
        return transactionElementList
