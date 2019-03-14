from optparse import OptionParser

parser = OptionParser()
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")
parser.add_option("-g", "--gtx", type="int", dest="gtx",
                  help="GTX on the AMC", metavar="gtx", default=0)
parser.add_option("--nevts", type="int", dest="nevts",
                  help="Number of events to count at each scan point", metavar="nevts", default=1000)
parser.add_option("--scanmin", type="int", dest="scanmin",
                  help="Minimum value of scan parameter", metavar="scanmin", default=0)
parser.add_option("--scanmax", type="int", dest="scanmax",
                  help="Maximum value of scan parameter", metavar="scanmax", default=254)
parser.add_option("--shelf", type="int", dest="shelf",default=1,
            	  help="uTCA shelf to access", metavar="shelf")
parser.add_option("-s","--slot", type="int", dest="slot",default=4,
                  help="slot in the uTCA of the AMC you are connceting too")
parser.add_option("--stepSize", type="int", dest="stepSize", 
                  help="Supply a step size to the scan from scanmin to scanmax", metavar="stepSize", default=1)
parser.add_option("--vfatmask", type="int", dest="vfatmask",
                  help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFF masks all VFATs)", metavar="vfatmask", default=0x0)
