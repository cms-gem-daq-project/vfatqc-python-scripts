'''
Common Hardware Interface Protocol System (CHIPS) logger

Just a simple logger.

Created on May 12, 2010

@author: Robert Frazier
'''

import logging
import sys
chipsLog = logging.getLogger("CHIPSLog")
#logHandler = logging.StreamHandler(sys.stdout)     # Use this to log to screen
logHandler = logging.FileHandler("ChipsBus.log")   # Use this to log to file
logFormatter = logging.Formatter("%(message)s")
logHandler.setFormatter(logFormatter)
chipsLog.addHandler(logHandler)
chipsLog.setLevel(logging.WARNING)  # Change this log threshold to one of the following: DEBUG INFO WARNING ERROR CRITICAL
