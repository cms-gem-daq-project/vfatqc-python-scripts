'''
Created on May 14, 2010

@author: Robert Frazier
'''
from ChipsException import ChipsException
from CommonTools import uInt32HexStr


# This is an enumeration of the different "Info Codes", that define packet direction and error status.
INFO_CODE_RESPONSE          = 0x0   # Host reports that the request was handled successfully.
INFO_CODE_BAD_HEADER        = 0x1   # Host reports that the client request had a bad header.
INFO_CODE_BUS_ERR_ON_RD     = 0x2   # Host reports that there was bus error on read.
INFO_CODE_BUS_ERR_ON_WR     = 0x3   # Host reports that there was a bus error on write.
INFO_CODE_BUS_TIMEOUT_ON_RD = 0x4   # Host reports that there was a bus timeout on read.
INFO_CODE_BUS_TIMEOUT_ON_WR = 0x5   # Host reports that there was a bus timeout on write.
INFO_CODE_REQUEST           = 0xf   # A client transaction request

# A mapping of meaningful strings for the various info-codes above.
_infoCodeInterpretation = { INFO_CODE_RESPONSE          : "The client request was handled successfully",
                            INFO_CODE_BAD_HEADER        : "The client request had a bad header",
                            INFO_CODE_BUS_ERR_ON_RD     : "The client request resulted in a bus-error-on-read",
                            INFO_CODE_BUS_ERR_ON_WR     : "The client request resulted in a bus-error-on-write",
                            INFO_CODE_BUS_TIMEOUT_ON_RD : "The client request resulted in a bus-read timeout",
                            INFO_CODE_BUS_TIMEOUT_ON_WR : "The client request resulted in a bus-write timeout",
                            INFO_CODE_REQUEST           : "Outgoing client request"  }

# This is an enumeration of the different codes for the different transaction types
TYPE_ID_READ           = 0x0  # Read transaction code
TYPE_ID_WRITE          = 0x1  # Write transaction code
TYPE_ID_NON_INCR_READ  = 0x2  # Non-Incrementing Read transaction code
TYPE_ID_NON_INCR_WRITE = 0x3  # Non-Incrementing Write transaction code
TYPE_ID_RMW_BITS       = 0x4  # Read-Modify-Write Bits transaction code
TYPE_ID_RMW_SUM        = 0x5  # Read-Modify-Write Sum transaction code
TYPE_ID_RSVD_ADDR_INFO = 0xE  # Reserved Address Info Request transaction code

# Request transaction element (i.e. controller-to-target) minimum body size
_minimumRequestBodySize = { TYPE_ID_READ           : 1,  # Read
                            TYPE_ID_WRITE          : 1,  # Write
                            TYPE_ID_RMW_BITS       : 3,  # Read-Modify-Write Bits
                            TYPE_ID_RMW_SUM        : 2,  # Read-Modify-Write Sum
                            TYPE_ID_NON_INCR_READ  : 1,  # Non-incrementing Read
                            TYPE_ID_NON_INCR_WRITE : 1,  # Non-incrementing Write
                            TYPE_ID_RSVD_ADDR_INFO : 0 } # Reserved Address Info request

# Response transaction element (i.e. target-to-controller) minimum body size
_minimumResponseBodySize = { TYPE_ID_READ           : 0,  # Read
                             TYPE_ID_WRITE          : 0,  # Write
                             TYPE_ID_RMW_BITS       : 1,  # Read-Modify-Write Bits
                             TYPE_ID_RMW_SUM        : 1,  # Read-Modify-Write Sum
                             TYPE_ID_NON_INCR_READ  : 0,  # Non-incrementing Read
                             TYPE_ID_NON_INCR_WRITE : 0,  # Non-incrementing Write
                             TYPE_ID_RSVD_ADDR_INFO : 2 } # Reserved Address Info request


def makeHeader(version, transactionId, words, typeId, infoCode):
        '''Returns a 32-bit IPbus transaction element header as created from individual header components.'''

        rawHeaderU32 =  ((version & 0xf) << 28)  | \
                        ((transactionId & 0xfff) << 16) | \
                        ((words & 0xff) << 8) | \
                        ((typeId & 0xf) << 4) | \
                        (infoCode & 0xf)

        return rawHeaderU32


def getExpectedBodySize(rawHeaderU32):
    '''Calculates the expected body size of an IPbus TransactionElement from the raw 32-bit header word'''

    result = 0
    typeId = getTypeId(rawHeaderU32)

    # Test if it's a known request/response typeId (doesn't matter which bodySize map we use)
    if typeId in _minimumResponseBodySize:

        # response from target to controller
        if getInfoCode(rawHeaderU32) == INFO_CODE_RESPONSE:
            if typeId == TYPE_ID_READ or typeId == TYPE_ID_NON_INCR_READ:
                result = getWords(rawHeaderU32) + _minimumResponseBodySize[typeId]
            else: result = _minimumResponseBodySize[typeId]

        # request from controller to target
        else:
            if typeId == TYPE_ID_WRITE or typeId == TYPE_ID_NON_INCR_WRITE:
                result = getWords(rawHeaderU32) + _minimumRequestBodySize[typeId]
            else: result = _minimumRequestBodySize[typeId]

    # Unknown transaction typeId.
    else:
        raise ChipsException("Cannot determine the expected body size from the given IPbus header '0x" + uInt32HexStr(rawHeaderU32) +
                             "', as it is of unknown transaction type '" + hex(typeId) + "'!")

    return result


def getVersion(rawHeaderU32):
    '''Returns the IPbus Version number contained within a raw IPbus Header'''
    return (rawHeaderU32 >> 28) & 0xf


def getWords(rawHeaderU32):
    '''Returns the value stored in the Words field of a raw IPbus Header'''
    return (rawHeaderU32 >> 8) & 0xff


def updateWords(rawHeaderU32, newWords):
    '''Returns the raw IPbus header but with the words field updated to the value specified'''
    return (rawHeaderU32 & 0xffff00ff | ((newWords & 0xff) << 8))


def getTransactionId(rawHeaderU32):
    '''Returns the Transaction ID number contained within a raw IPbus Header'''
    return (rawHeaderU32 >> 16) & 0xfff


def getTypeId(rawHeaderU32):
    '''Returns the Type ID Code contained within a raw IPbus Header'''
    return (rawHeaderU32 >> 4) & 0xf


def getInfoCode(rawHeaderU32):
    '''Returns the Info Code contained within a raw IPbus Header'''
    return rawHeaderU32 & 0xf


def updateInfoCode(rawHeaderU32, newInfoCode):
    '''Returns the raw IPbus header but with the Info Code updated to the value specified'''
    return (rawHeaderU32 & 0xfffffff0) | (newInfoCode & 0xf)


def isRequestHeader(rawHeaderU32):
    '''Returns true if the header is a request header (i.e. from client to target device)'''
    return (getInfoCode(rawHeaderU32) == INFO_CODE_REQUEST)


def isResponseHeader(rawHeaderU32):
    '''Returns true if the header is any kind of response header (i.e. either a success or error response).'''
    return not isRequestHeader(rawHeaderU32)


def isResponseSuccessHeader(rawHeaderU32):
    '''Returns true if the header is a successful host response header'''
    return (getInfoCode(rawHeaderU32) == INFO_CODE_RESPONSE)


def isResponseErrorHeader(rawHeaderU32):
    '''Returns true if the header is a host response error header'''
    return isResponseHeader(rawHeaderU32) and not isResponseSuccessHeader(rawHeaderU32)


def interpretInfoCode(infoCode):
    '''Returns a user-readable sentence string of the meaning of a given Info Code.'''
    if infoCode in _infoCodeInterpretation:
        return _infoCodeInterpretation[infoCode]
    else:
        return "The IPbus header Info Code '" + hex(0xf & infoCode) + "' is undefined/reserved!"

