import sys, os, time

# Get IPBus
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/ipbus")
from PyChipsUser import *

#
class GLIB:

    ipbus = False

    def __init__(self, ipaddress = 0):
        if (ipaddress == 0):
            f = open(os.path.dirname(os.path.abspath(__file__)) + "/glib_ip.dat", "r")
            ipaddress = f.readline().strip()
            f.close()
        ipbusAddrTable = AddressTable(os.path.dirname(os.path.abspath(__file__)) + "/register_mapping.dat")
        self.ipbus = ChipsBusUdp(ipbusAddrTable, ipaddress, 50001)

    def get(self, register):
        try:
            return self.ipbus.read(register)
        except ChipsException, e:
            pass

    def set(self, register, value): 
        try:
            return self.ipbus.write(register, value)
        except ChipsException,e:
            pass

    def fifoRead(self, register, depth = 1):
        try:
            return self.ipbus.fifoRead(register, depth)
        except ChipsException,e:
            pass

    def blockRead(self, register, depth = 1):
        try:
            return self.ipbus.blockRead(register, depth)
        except ChipsException,e:
            pass

    def fifoWrite(self, register, data):
        try:
            return self.ipbus.fifoWrite(register, data)
        except ChipsException,e:
            pass

    def blockWrite(self, register, data):
        try:
            return self.ipbus.blockWrite(register, depth)
        except ChipsException,e:
            pass
