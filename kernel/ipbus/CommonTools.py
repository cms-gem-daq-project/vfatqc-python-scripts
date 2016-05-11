'''
Tools common to the entire project

Various tools, including tools to deal with the general annoyance of Python when you really 
want to work with a well-defined 32-bit unsigned integer type.

Created on May 12, 2010
@author: Robert Frazier
'''

from ChipsException import ChipsException


def pyChipsVersion():
    """Returns the version number of the PyChips release as a string e.g.: 'PyChips vX.Y.Z'"""
    return "PyChips v1.5.0_pre2"


def uInt32Compatible(integer):
    """Returns true if the integer provided is not negative and can be express within 32-bits."""
    return integer < 0x100000000 and integer >= 0

def uInt32HexStr(uInt32, checkValidUInt32 = False):
    """Return a string of a 32-bit unsigned integer without any minus signs, or other stupidity.
    
    I can't believe I actually had to to write this function.  Python always manages to 
    fuckup displaying unsigned integers somehow or other.
    """
    if checkValidUInt32:
        if not uInt32Compatible(uInt32):
            raise ChipsException("The value: " + hex(uInt32) + " is not a valid 32-bit unsigned integer!")
    bigEnd = (uInt32 >> 16) & 0xffff
    littleEnd = uInt32 & 0xffff
    result = "%(#1)04x%(#2)04x" % { "#1" : bigEnd, "#2" : littleEnd }
    return result

def uInt32BitFlip(uInt32, checkValidUInt32 = False):
    """Flip the bits of a 32-bit unsigned number, avoiding negative numbers or other stupidity.
    
    I can't believe I had to write this function either.  Using the ~ operator (which is the
    bitwise complement operator) sometimes results in a negative number, which then breaks
    the socket.htonl() or socket.ntohl() fuctions
    """
    if checkValidUInt32:
        if not uInt32Compatible(uInt32):
            raise ChipsException("The value: " + hex(uInt32) + " is not a valid 32-bit unsigned integer!")
    if uInt32 >= 0: return 0xffffffff ^ (0xffffffff & uInt32)
    return 0xffffffff & ~uInt32

def uInt32HexListStr(uInt32List):
    """Converts a list of 32-bit unsigned numbers into a pretty string - basically a column of constant width 32-bit hex."""
    
    outputStr = ""
    for value in uInt32List:
        outputStr += "\n\t" + uInt32HexStr(value)
    outputStr += "\n"
    return outputStr

def uInt32HexDualListStr(uInt32List1, uInt32List2):
    """Returns a pretty string of two 32-bit unsigned hex lists in columns side by side, for easy comparison
    
    uInt32List1 and uInt32List2: Lists of equal length containing 32-bit unsigned values.
    Any differences are marked with a != sign between the two columns.
    """  
    minListLength = len(uInt32List1)
    if len(uInt32List2) < minListLength: minListLength = len(uInt32List2)
    outputStr = ""
    for i in range(minListLength):
        val1 = uInt32List1[i]
        val2 = uInt32List2[i]
        middle = "          "
        if val1 != val2: middle = "    !=    "     
        outputStr += "\n\t" + uInt32HexStr(val1) + middle + uInt32HexStr(val2)
    outputStr += "\n"
    return outputStr

def uInt8HexStr(uInt8):
    """Return a string of an 8-bit unsigned integer without any minus signs, or other possible stupidity."""
    
    croppedTo8bit = uInt8 & 0xff  # ensure the value is only 8 bit.
    result = "%(#1)02x" % { "#1" : croppedTo8bit }
    return result