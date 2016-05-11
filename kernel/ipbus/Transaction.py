'''
Created on May 12, 2010

@author: Robert Frazier
'''

# System imports
import logging
import socket

# Project imports
from ChipsLog import chipsLog
from ChipsException import ChipsException
from CommonTools import uInt32HexStr
from SerDes import SerDes
from IPbusHeader import getTransactionId, getTypeId, getInfoCode, isRequestHeader, isResponseErrorHeader, interpretInfoCode

class Transaction(object):

    '''Used for storing the details of a transaction in terms of serial/non-serial requests and responses'''

    def __init__(self):
        object.__init__(self)
        self.addr = ("", 0)  # Tuple of host string and port number, e.g. ("192.168.0.1", 50001) 
        self.requests = []  # Requests: a list of TransactionElement objects
        self.serialRequests = ""  # For holding the serialised requests payload string
        self.responses = []  # Responses: a list of TransactionElement objects
        self.serialResponses = ""  # For holding the serialised responses payload string
        self._serdes = SerDes() # For serialising/deserialising transactions


    @classmethod
    def constructHostTransaction(cls, packetPayload, clientAddr):
        """Constructs a typical host Transaction object instance
        
        Usage: the host has just received a serial packetPayload string from a
        client with clientAddr.  clientAddr is a tuple of ("hostIP", portNumber),
        e.g.  ("192.168.0.1", 50001).  Thus, you want to make a Transaction object
        with this data set via constructor.
        """
        transaction = cls()
        transaction.addr = clientAddr
        transaction.serialRequests = packetPayload
        return transaction


    @classmethod
    def constructClientTransaction(cls, transactionElementList, targetAddr):
        """Constructs a typical client Transaction object instance
        
        Usage: you want to send the host (i.e. hardware) a read/write/etc
        request, and have already formulated the TransactionElementList that
        needs to be serialised for sending to the host.  The argument targetAddr
        is the host's IP address and port number in the form of a tupe like this:
        ("hostIP", portNumber), e.g. ("192.168.0.2", 50002).
        """
        transaction = cls()
        transaction.addr = targetAddr
        transaction.requests = transactionElementList
        return transaction


    def getHostAddr(self):
        """Returns the host IP address"""
        return self.addr[0]


    def appendRequest(self, transactionElement):
        """Append a request to the transaction list"""
        self.requests.append(transactionElement)

        
    def appendResponse(self, transactionElement):
        """Append a response to the transaction list"""
        self.responses.append(transactionElement)


    def serialiseRequests(self):
        """Serialise current requests list - the result is put into the serialisedRequests string"""
        self.serialRequests = self._serdes.serialise(self.requests)

    
    def serialiseResponses(self):
        """Serialise current responses list - the result is put into the serialisedResponses string"""
        self.serialResponses = self._serdes.serialise(self.responses)

        
    def deserialiseRequests(self):
        """Deserialise current serialisedRequests string - the result is put into the requests list"""
        self.requests = self._serdes.deserialise(self.serialRequests)

    
    def deserialiseResponses(self):
        """Deserialise current serialisedResponses string - the result is put into the responses list"""
        self.responses = self._serdes.deserialise(self.serialResponses) 

    def doTransactionChecks(self):
        """Performs a generic set of client transaction checks on all transaction elements in the request/response lists"""

        if len(self.requests) != len(self.responses):
            raise ChipsException("Transaction error: incorrect number of responses returned!")

        for iElement in range(len(self.requests)):

            request = self.requests[iElement]
            response = self.responses[iElement]
            requestHeader = request.getHeader()
            responseHeader = response.getHeader()
            
            if getTypeId(requestHeader) != getTypeId(responseHeader):
                raise ChipsException("Transaction error from '" + self.getHostAddr() + " (header=0x" + uInt32HexStr(responseHeader) + "): " \
                                     "request and response transaction types do not match; expected '" + hex(getTypeId(requestHeader)) + 
                                     "' but got '" + hex(getTypeId(responseHeader)) + "'!")
                                     
            if getTransactionId(requestHeader) != getTransactionId(responseHeader):
                raise ChipsException("Transaction error from '" + self.getHostAddr() + " (header=0x" + uInt32HexStr(responseHeader) + "): " \
                                     "request and response transactions IDs do not match; expected '" + str(getTransactionId(requestHeader)) + 
                                     "' but got '" + str(getTransactionId(responseHeader)) + "'!")
                                     
            if isRequestHeader(responseHeader):
                raise ChipsException("Transaction error from '" + self.getHostAddr() + " (header=0x" + uInt32HexStr(responseHeader) + "): " \
                                     "the received response for transaction ID " + str(getTransactionId(responseHeader)) + " has an INFO CODE " \
                                     "that declares it as a request!")
                                                      
            if isResponseErrorHeader(responseHeader):
                raise ChipsException("Transaction error from '" + self.getHostAddr() + " (header=0x" + uInt32HexStr(responseHeader) + "): " \
                                     "the host reports the following error occurred (INFO CODE = " + hex(getInfoCode(responseHeader)) +
                                     ") whilst processing transaction ID " + str(getTransactionId(responseHeader)) + ": '" + 
                                     interpretInfoCode(getInfoCode(responseHeader)) + "'!")
                                     
            if not response.validBodySize():
                raise ChipsException("Transaction error from '" + self.getHostAddr() + " (header=0x" + uInt32HexStr(responseHeader) + "): " \
                                     "incorrect response body size for transaction number " + str(getTransactionId(responseHeader)) + "!")
