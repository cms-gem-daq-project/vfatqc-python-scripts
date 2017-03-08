from plot_scurve import *

parser = OptionParser()
parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveFitData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-v", "--vfat", type="int", dest="vfat",
                  help="Specify VFAT to plot", metavar="vfat")
parser.add_option("-ch", "--channel", type="int", dest="channel",
                  help="Specify channel to plot", metavar="channel")
parser.add_option("-o","--overlay", action="store_true", dest="overlay_fit",
                  help="Make overlay of fit result on scurve", metavar="overlay_fit")
parser.add_option("-c","--channels_yes", action="store_true", dest="channel_yes",
                  help="Passing a channel number instead of strip number", metavar="channel_yes")
(options, args) = parser.parse_args()
filename = options.filename
overlay_fit = options.overlay_fit
channel_yes = options.channel_yes
vfat = options.vfat
channel = options.channel
plot_scurve(vfat, channel, filename, overlay_fit, channel_yes)
