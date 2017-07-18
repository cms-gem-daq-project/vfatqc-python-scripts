#from gempython.utils.standardopts import parser
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                  help="print extra debugging information", metavar="debug")
parser.add_option("-i", "--infilename", type="string", dest="filename",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-p","--panasonic", action="store_true", dest="PanPin",
                  help="Make plots vs Panasonic pins instead of strips", metavar="PanPin")
parser.add_option("-o", "--outfilename", type="string", dest="outfilename",
                  help="Specify Output Filename", metavar="outfilename")
parser.add_option("--scandate", type="string", dest="scandate", default="current",
                  help="Specify specific date to analyze", metavar="scandate")
parser.add_option("--scandatetrim", type="string", dest="scandatetrim", default=None,
                  help="Specify the scan date of the trim run that corresponds to the chConfig.txt used in scandate", metavar="scandatetrim")
parser.add_option("-t", "--type", type="string", dest="GEBtype", default="long",
                  help="Specify GEB (long/short)", metavar="GEBtype")
parser.add_option("--vfatmask", type="int", dest="vfatmask", 
                  help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFF masks all VFATs)", metavar="vfatmask", default=0x0)
parser.add_option("--ztrim", type="float", dest="ztrim", default=0.0,
                  help="Specify the p value of the trim", metavar="ztrim")
