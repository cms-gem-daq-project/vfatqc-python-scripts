'''
Common imports for using PyChips as a standard user (normal amount of logging)

@author: Robert Frazier

May 2010
'''

from ChipsBus import ChipsBus, ChipsBusUdp, ChipsBusTcp

from AddressTable import AddressTable

from CommonTools import *
##print pyChipsVersion()

from ChipsLog import chipsLog, logging
chipsLog.setLevel(logging.INFO)