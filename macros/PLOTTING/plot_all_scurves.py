from plot_scurve import *

parser = OptionParser()
parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveFitData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-o","--overlay", action="store_true", dest="overlay_fit",
                  help="Make overlay of fit result on scurve", metavar="overlay_fit")
parser.add_option("-c","--channels", action="store_true", dest="channel_yes",
                  help="Passing a channel number instead of strip number", metavar="channel_yes")
(options, args) = parser.parse_args()
filename = options.filename
overlay_fit = options.overlay_fit
channel_yes = options.channel_yes

plot_scurve(5, 3, filename, overlay_fit, channel_yes)
