from plot_scurve import *

parser = OptionParser()
parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveFitData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-v", "--vfat", type="int", dest="vfat",
                  help="Specify VFAT to plot", metavar="vfat")
parser.add_option("-s", "--strip", type="int", dest="strip",
                  help="Specify strip to plot", metavar="strip")
parser.add_option("-o","--overlay", action="store_true", dest="overlay_fit",
                  help="Make overlay of fit result on scurve", metavar="overlay_fit")
parser.add_option("-c","--channels_yes", action="store_true", dest="channel_yes",
                  help="Passing a channel number instead of strip number", metavar="channel_yes")
(options, args) = parser.parse_args()
filename = options.filename
overlay_fit = options.overlay_fit
channel_yes = options.channel_yes
vfat = options.vfat
strip = options.strip

thr = []
Scurves = []
fitF = TFile(filename)
for event in fitF.scurveFitTree:
    if (event.vthr) not in thr:
        thr.append(event.vthr)
        pass
    pass
print thr

canvas = TCanvas('canvas', 'canvas', 500, 500)
canvas.cd()
for thresh in thr:
    for event in fitF.scurveFitTree:
        if (event.vthr == thresh) and (event.vfatN == vfat) and (event.vfatstrip == strip):
#            Scurve = event.scurve_h
            Scurves.append(event.scurve_h)
            (event.scurve_h).Draw('SAME')
#            canvas.Update()
            pass
        pass
    pass
canvas.Update()
canvas.SaveAs('Scurve_vs_Thresh_VFAT_%i_Strip_%i.png'%(vfat, strip))
