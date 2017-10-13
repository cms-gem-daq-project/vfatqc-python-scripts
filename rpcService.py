from ctypes import *
from gempython.utils.wrappers import envCheck

import os, sys
sys.path.append('${GEM_PYTHON_PATH}')

envCheck("XHAL_ROOT")

# Define the connection
lib = CDLL(os.getenv("XHAL_ROOT")+"/lib/x86_64/librpcman.so")
rpc_connect = lib.init
rpc_connect.argtypes = [c_char_p]
rpc_connect.restype = c_uint

# Define VFAT3 Configuration
configureVFAT3s = lib.configureVFAT3s
configureVFAT3s.argTypes = [ c_uint, c_uint ]
configureVFAT3s.restype = c_uint

# Define TTC Configuration
ttcGenConf = lib.ttcGenConf
ttcGenConf.restype = c_uint
ttcGenConf.argtypes = [c_uint, c_uint]

# Define scan module
genScan = lib.genScan
genScan.restype = c_uint
genScan.argtypes = [c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_char_p, POINTER(c_uint32)]
