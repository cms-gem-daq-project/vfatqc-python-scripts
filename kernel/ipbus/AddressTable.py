'''
@author: Robert Frazier

May 2010
'''


# Project imports
from AddressTableItem import AddressTableItem
from CommonTools import uInt32Compatible
from ChipsException import ChipsException


class AddressTable(object):
    '''Address table class to hold address table items and read in address tables from file

    The format is very simple.  Each line should contain a register name,
    a 32-bit (hex) register address, and a 32-bit (hex) register mask, in
    that order.  Any further words/values on that line are then ignored.
    Empty lines or lines starting with a "*" character are also ignored.
    Note that the IPbus protocol, and hence PyChips assumes 32-bit word
    addressing, allowing up to 2^34 bytes to be addressed.  I.e. each
    address points to a 32-bit word.
    
    An example is as follows:
    
    * RegName              RegAddr      RegMask      R     W     Description
    *---------------------------------------------------------------------------------------------
    someRegister           00000001     ffffffff     1     0     Any text you like here
    anotherRegister_low    0000000f     0000ffff     1     1     Bottom 16 bits for one purpose
    anotherRegister_high   0000000f     ffff0000     1     1     Top 16 bits for another purpose.
    *---------------------------------------------------------------------------------------------
    '''

    def __init__(self, addressTableFile):
        object.__init__(self)
        self.items = {}
        self.fileName = addressTableFile
        self._readAddrTable(addressTableFile)


    def getItem(self, registerName):
        """Returns the AddressTableItem object that corresponds to a particular register name."""
        if self.checkItem(registerName):
            return self.items[registerName]
        else:
            raise ChipsException("Register '" + registerName + "' does not exist in the address table file '" + self.fileName + "'!")


    def checkItem(self, registerName):
        """Returns True if registerName is present in the address table; returns False if it's not."""
        if registerName in self.items:
            return True
        return False


    def _readAddrTable(self, addressTableFile):
        '''Read in an address table from the specified file'''

        file = open(addressTableFile, 'r')
        line = file.readline() # Get the first line
        lineNum = 1

        while len(line) != 0:  # i.e. not the end of the file
            words = line.split()   # Split up the line into words by its whitespace
            if len(words) != 0:  # A blank line (or a line with just whitespace).
                if line[0] != '*':  # Not a commented line
                    if len(words) < 5:
                        raise ChipsException("Line " + str(lineNum) + " of file '" + addressTableFile + 
                                             "' does not conform to file format expectations!")
                    try:
                        regName = words[0]
                        regAddr = int(words[1], 16)
                        regMask = int(words[2], 16)
                        regRead = int(words[3])
                        regWrite= int(words[4])
                    except Exception, err:
                        raise ChipsException("Line " + str(lineNum) + " of file '" + addressTableFile + 
                                             "' does not conform to file format expectations! (Detail: " + str(err))
                    if regName in self.items:
                        raise ChipsException("Register '" + regName + "' is included in the file '"
                                             + addressTableFile + "' more than once!")
                    if not(uInt32Compatible(regAddr) and uInt32Compatible(regMask)):
                        raise ChipsException("Register address or mask on line " + str(lineNum) +
                                             " of file '" + addressTableFile + "' is not " \
                                             "a valid 32-bit unsigned number!")
                    if regMask == 0: raise ChipsException("Register mask on line " + str(lineNum) +
                                                          " of file '" + addressTableFile + 
                                                          "' is zero! This is not allowed!")
                    if regRead != 0 and regRead != 1:raise ChipsException("Read flag on line " +
                                                                          str(lineNum) + " of file '" +
                                                                          addressTableFile + "' is not one or zero!")
                    if regWrite != 0 and regWrite != 1: raise ChipsException("Write flag on line " +
                                                                             str(lineNum) + " of file '" +
                                                                             addressTableFile + "' is not one or zero!")

                    item = AddressTableItem(regName, regAddr, regMask, regRead, regWrite)
                    self.items[regName] = item
            line = file.readline()  # Get the next line and start again.
            lineNum += 1
