
from gempython.utils.standardopts import parser

parser.add_option("--namc", type="int", dest="namc",
                  help="Number of register tests to perform on the amc (default is 100)", metavar="namc", default=100)
parser.add_option("--noh", type="int", dest="noh",
                  help="Number of register tests to perform on the OptoHybrid (default is 100)", metavar="noh", default=100)
parser.add_option("--ni2c", type="int", dest="ni2c",
                  help="Number of I2C tests to perform on the VFAT2s (default is 100)", metavar="ni2c", default=100)
parser.add_option("--ntrk", type="int", dest="ntrk",
                  help="Number of tracking data packets to readout (default is 1000)", metavar="ntrk", default=1000)
parser.add_option("--writeout", action="store_true", dest="writeout",
                  help="Write the data to disk when testing the rate", metavar="writeout")
parser.add_option("--tests", type="string", dest="tests",default="A,B,E,F",
                  help="Tests to run, default is all", metavar="tests")
parser.add_option("--doLatency", action="store_true", dest="doLatency",
                  metavar="doLatency",
                  help="[OPTIONAL] Run latency scan to determine the latency value")
parser.add_option("--QC3test", action="store_true", dest="doQC3",
                  metavar="doQC3",
                  help="[OPTIONAL] Run a shortened test after covers have been applied")
parser.add_option("--ztrim", type="float", dest="ztrim", default=0.0,
                  help="Specify the p value of the trim", metavar="ztrim")
parser.add_option("--scanmin", type="int", dest="scanmin",
                  help="Minimum value of scan parameter", metavar="scanmin", default=0)
parser.add_option("--scanmax", type="int", dest="scanmax",
                  help="Maximum value of scan parameter", metavar="scanmax", default=254)
parser.add_option("--nevts", type="int", dest="nevts",
                  help="Number of events to count at each scan point", metavar="nevts", default=1000)
