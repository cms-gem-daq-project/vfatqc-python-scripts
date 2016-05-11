'''
Created on May 12, 2010

@author: Robert Frazier
'''

# System imports
import socket
from Queue import Queue
from threading import Thread
from time import sleep

# Project imports
from ChipsLog import chipsLog
from Transaction import Transaction
from TransactionElement import TransactionElement
import IPbusHeader
from CommonTools import uInt32HexStr
from ChipsException import ChipsException


class DummyHardwareBase(Thread):
    """Represents a dummy hardware device using the IPbus control system.
    
    This class can receive, act on, and respond to IPbus packets.  It will
    keep track of registers that are written to, but its initial register
    state is zero throughout the entire address space.
    
    It operates with two threads.  The main program thread receives incoming
    packets and queues them for action and response by a transaction handler
    thread.
    
    Note: Requesting a read on register address 0xffffffff will be interpreted
    as a request to reset the internal state of the hardware, so all registers
    will be set to zero.
    """

    SOCKET_BUFFER_SIZE = 32768
    REQUEST_QUEUE_SIZE = 1024


    def __init__(self):
        Thread.__init__(self)
        self._registers = {}
        self._transaction_queue = Queue(DummyHardware.REQUEST_QUEUE_SIZE)
        self._transactionCounter = 0
        self.stopServing = False
        # This maps request type number to the function that handles the request.
        self._requestTypeHandlerMap = {IPbusHeader.TYPE_ID_READ           : self._handleReadRequest,
                                       IPbusHeader.TYPE_ID_WRITE          : self._handleWriteRequest,
                                       IPbusHeader.TYPE_ID_NON_INCR_READ  : self._handleFifoReadRequest,
                                       IPbusHeader.TYPE_ID_NON_INCR_WRITE : self._handleFifoWriteRequest,
                                       IPbusHeader.TYPE_ID_RMW_BITS       : self._handleReadModifyWriteBitsRequest,
                                       IPbusHeader.TYPE_ID_RMW_SUM        : self._handleReadModifyWriteSumRequest,
                                       IPbusHeader.TYPE_ID_RSVD_ADDR_INFO : self._handleGetReservedAddrInfoRequest}

    
    def serveForever(self):
        raise NotImplementedError("DummyHardwareBase is an Abstract Base Class!\n" \
                                  "Please use a concrete implementation such as "\
                                  "DummyHardwareUdp or DummyHardwareTcp!")


    def run(self):
        """Start the transaction handler thread"""
        chipsLog.info("Transaction handler thread started")
        while not self.stopServing:
            if self._transaction_queue.empty():
                sleep(0.001)
            else:
                transaction = self._transaction_queue.get()
                self._actAndRespond(transaction)
        chipsLog.info("Transaction handler thread stopping")


    def closeSockets(self):
        """Allows you to manually close any sockets that may have been opened."""
        try:
            self._socket.close()
            chipsLog.debug("Socket closed successfully.")
        except:
            chipsLog.warn("Error closing socket!")


    def _actAndRespond(self, transaction):
        """Performs the required action and returns the response for a given transaction"""
        self._transactionCounter += 1
        chipsLog.debug("*** Performing transaction #" + str(self._transactionCounter) + " ***")
        try:
            transaction.deserialiseRequests()
    
            for request in transaction.requests:
                transaction.appendResponse(self._requestTypeHandlerMap[IPbusHeader.getTypeId(request.getHeader())](request))
            
            transaction.serialiseResponses()
            chipsLog.debug("Sending response packet")
            self._socketSend(transaction)
            chipsLog.debug("Response packet sent!")
            chipsLog.debug("*** Transaction #" + str(self._transactionCounter) + " completed! ***\n")
        except ChipsException, err:
            chipsLog.error("ERROR! Transaction #" + str(self._transactionCounter) + 
                           " could not be successfully processed:\n\t" + str(err))


    def _socketSend(self, transaction):
        raise NotImplementedError("DummyHardwareBase is an Abstract Base Class!\n" \
                                  "Please use a concrete implementation such as "\
                                  "DummyHardwareUdp or DummyHardwareTcp!")


    def _handleReadRequest(self, request):
        requestHeader = request.getHeader()
        words = IPbusHeader.getWords(requestHeader)
        baseAddr = request.getBody()[0]
        chipsLog.debug("Read requested on Addr=0x" + uInt32HexStr(baseAddr))

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(requestHeader, IPbusHeader.INFO_CODE_RESPONSE)

        # The (baseAddr & 0xffffffff) forces baseAddr to be in unsigned form (i.e. 0xfffffffc, say, rather than -4)
        if (baseAddr & 0xffffffff) == 0xffffffff:  # A read on this register is a Dummy Hardware Reset Request.
            chipsLog.info("** Dummy Hardware reset request received! Zeroing all registers. **")
            self._registers.clear()
        
        responseBody = []
        appendToResponseBody = responseBody.append  # This is for a speed optimisation  
        
        for offset in range(words):
            currentReg = baseAddr + offset  
            # Create these registers if they don't already exist.
            if currentReg not in self._registers:
                self._registers[currentReg] = 0
            appendToResponseBody(self._registers[currentReg])
        return TransactionElement.makeFromHeaderAndBody(responseHeader, responseBody)


    def _handleWriteRequest(self, request):
        requestHeader = request.getHeader()
        words = IPbusHeader.getWords(requestHeader)
        requestBody = request.getBody()
        baseAddr = requestBody[0]
        chipsLog.debug("Write requested on Addr=0x" + uInt32HexStr(baseAddr))

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(requestHeader, IPbusHeader.INFO_CODE_RESPONSE)

        for offset in range(words):
            currentReg = baseAddr + offset  
            self._registers[currentReg] = requestBody[offset + 1]
        return TransactionElement.makeFromHeaderAndBody(responseHeader)


    def _handleFifoReadRequest(self, request):
        requestHeader = request.getHeader()
        words = IPbusHeader.getWords(requestHeader)
        fifoAddr = request.getBody()[0]
        chipsLog.debug("FIFO read requested on Addr=0x" + uInt32HexStr(fifoAddr))

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(requestHeader, IPbusHeader.INFO_CODE_RESPONSE)

        # Create the register if they don't already exist in our memory space
        if fifoAddr not in self._registers:
            self._registers[fifoAddr] = 0

        # Obviously we don't really have a FIFO, so we'll just have to return the value stored
        # at the FIFO's address many times...
        value = self._registers[fifoAddr]
        responseBody = [value for iReads in range(words)]
        return TransactionElement.makeFromHeaderAndBody(responseHeader, responseBody)


    def _handleFifoWriteRequest(self, request):
        requestHeader = request.getHeader()
        requestBody = request.getBody()
        fifoAddr = requestBody[0]
        chipsLog.debug("FIFO write requested on Addr=0x" + uInt32HexStr(fifoAddr))

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(requestHeader, IPbusHeader.INFO_CODE_RESPONSE)

        # Obviously we don't really have a FIFO, we just have a single register at the address of the supposed
        # FIFO.  So, whatever the last value written into the FIFO is, this will be the value this register will
        # take.  We ignore all the previous "writes" to the FIFO.
        self._registers[fifoAddr] = requestBody[-1]

        return TransactionElement.makeFromHeaderAndBody(responseHeader)


    def _handleReadModifyWriteBitsRequest(self, request):
        requestBody = request.getBody()
        addr = requestBody[0]
        andTerm = requestBody[1]  # The and term is the bitwise complement of the register mask (i.e. mask = ~andTerm)
        orTerm = requestBody[2]
        chipsLog.debug("Read/Modify/Write-bits requested on Addr=0x" + uInt32HexStr(addr))
        
        # Create the register if it doesn't already exist.
        if addr not in self._registers: self._registers[addr] = 0
        
        updatedValue = (self._registers[addr] & andTerm) | (orTerm)
        self._registers[addr] = updatedValue

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(request.getHeader(), IPbusHeader.INFO_CODE_RESPONSE)

        return TransactionElement.makeFromHeaderAndBody(responseHeader, [updatedValue])


    def _handleReadModifyWriteSumRequest(self, request):
        requestBody = request.getBody()
        addr = requestBody[0]
        addend = requestBody[1]  # The value we add to the existing value
        chipsLog.debug("Read/Modify/Write-sum requested on Addr=0x" + uInt32HexStr(addr))
        
        # Create the register if it doesn't already exist.
        if addr not in self._registers: self._registers[addr] = 0
        
        updatedValue = (self._registers[addr] + addend) & 0xffffffff
        self._registers[addr] = updatedValue

        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(request.getHeader(), IPbusHeader.INFO_CODE_RESPONSE)

        return TransactionElement.makeFromHeaderAndBody(responseHeader, [updatedValue])


    def _handleGetReservedAddrInfoRequest(self, request):
        chipsLog.debug("Reserved Address Info transaction requested")
        # Response header is the request header but with the Info Code field changed to INFO_CODE_RESPONSE
        responseHeader = IPbusHeader.updateInfoCode(request.getHeader(), IPbusHeader.INFO_CODE_RESPONSE)
        responseHeader = IPbusHeader.updateWords(responseHeader, 2)
        # Returning zeros for the response body, as no real idea what else it should be.
        return TransactionElement.makeFromHeaderAndBody(responseHeader, [0,0])


    def _stopServingAndJoinThreads(self):
        self.stopServing = True
        self.join(1)  #Let's wait for the transaction handler thread to complete normally.
        chipsLog.info("Dummy hardware server stopping.")


class DummyHardwareUdp(DummyHardwareBase):

    def __init__(self, port = 50001):
        DummyHardwareBase.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self._socket.bind(('', port))        


    def serveForever(self):
        """The only function any user of this class needs to run!
        
        Receives, acts on, and responds to UDP control packets as the Mini-T (or similar hardware) would.
        Packets are received by the main thread and queued for action and response by a second thread.
        """
        chipsLog.info("Dummy Hardware UDP Server starting")
        # This starts the packet "act and respond" handler thread
        self.start()

        while not self.stopServing:
            try:
                data, addr = self._socket.recvfrom(DummyHardware.SOCKET_BUFFER_SIZE)
            except KeyboardInterrupt:
                chipsLog.warning("\nKeyboard interrupt (ctrl-c) received whilst waiting for incoming UDP packet")
                self._stopServingAndJoinThreads()
                return
            except:
                chipsLog.warning("\nException caught whilst waiting for incoming UDP packet")
                self._stopServingAndJoinThreads()
                return

            if not data:
                chipsLog.warning("Socket received an empty packet from " + repr(addr) + \
                                 ".  Assuming socket now closed.\nTerminating dummy hardware server...")
                self._stopServingAndJoinThreads()
                return
            else:
                chipsLog.debug("\nReceived packet from " + repr(addr))
                transaction = Transaction.constructHostTransaction(data, addr)
                self._transaction_queue.put(transaction)


    def _socketSend(self, transaction):
        self._socket.sendto(transaction.serialResponses, transaction.addr)
        
        

class DummyHardwareTcp(DummyHardwareBase):

    def __init__(self, port = 50002):
        DummyHardwareBase.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
        self._socket.bind(('', port))     
        self._socket.listen(1)  # TCP-specific: we will only accept a single TCP connection
        self._connectedSocket = None  # Once we have a TCP connection, this will be used for responding to the client.


    def closeSockets(self):
        """Allows you to manually close any sockets that may have been opened."""
        if self._connectedSocket != None:
            try:
                self._connectedSocket.close()
                chipsLog.debug("Connected TCP socket closed successfully.")
            except:
                chipsLog.debug("Error closing connected TCP socket!")
        DummyHardwareBase.closeSockets(self)


    def serveForever(self):
        """The only function any user of this class needs to run!
        
        Receives, acts on, and responds to TCP control packets as the Mini-T (or similar hardware) would.
        Packets are received by the main thread and queued for action and response by a second thread.
        """
        chipsLog.info("Dummy Hardware TCP Server starting")
        # This starts the packet "act and respond" handler thread
        self.start()

        try:
            chipsLog.debug("Awaiting connection...")
            self._connectedSocket, addr = self._socket.accept()  # TCP
            chipsLog.debug("Client connection accepted.")            
        except KeyboardInterrupt:
            chipsLog.warning("\nKeyboard interrupt (ctrl-c) received whilst waiting for a TCP connection")
            self._stopServingAndJoinThreads()
            return            

        while not self.stopServing:
            try:
                data = self._connectedSocket.recv(DummyHardware.SOCKET_BUFFER_SIZE)  # TCP
            except KeyboardInterrupt:
                chipsLog.warning("\nKeyboard interrupt (ctrl-c) received whilst waiting for incoming TCP packet")
                self._stopServingAndJoinThreads()
                return
            except:
                chipsLog.warning("\nException caught whilst waiting for incoming TCP packet")
                self._stopServingAndJoinThreads()
                return

            if not data:
                chipsLog.debug("TCP socket received an empty packet from " + repr(addr) + ": assuming connection closed.")
                try:
                    chipsLog.debug("Awaiting new connection...")
                    self._connectedSocket, addr = self._socket.accept()  # TCP
                    chipsLog.debug("Client connection accepted.")            
                    continue
                except KeyboardInterrupt:
                    chipsLog.warning("\nKeyboard interrupt (ctrl-c) received whilst waiting for a TCP connection")
                    self._stopServingAndJoinThreads()
                    return            

            chipsLog.debug("\nReceived TCP packet from " + repr(addr))
            transaction = Transaction.constructHostTransaction(data, addr)
            self._transaction_queue.put(transaction)

        chipsLog.info("Dummy Hardware TCP Server stopping.")


    def _socketSend(self, transaction):
        self._connectedSocket.send(transaction.serialResponses)  # TCP-specific


class DummyHardware(DummyHardwareUdp):
    """Deprecated!  Essentially now just an alias for DummyHardwareUdp"""
    def __init__(self, port = 50001):
        DummyHardwareUdp.__init__(self, port)
        chipsLog.warning("Please note: this class has been deprecated - use DummyHardwareUdp in the future.")
