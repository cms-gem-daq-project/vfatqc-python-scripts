from optparse import OptionParser

parser = OptionParser()
parser.add_option("-i", "--infilename", type="string", dest="filename", default="SCurveFitData.root",
                  help="Specify Input Filename", metavar="filename")
parser.add_option("-v", "--vfat", type="int", dest="vfat",
                  help="Specify VFAT to plot", metavar="vfat")
parser.add_option("-s", "--strip", type="int", dest="strip",
                  help="Specify strip or channel to plot", metavar="strip")
parser.add_option("-c","--channels", action="store_true", dest="channels",
                  help="Make plots vs channels instead of strips", metavar="channels")

(options, args) = parser.parse_args()


def plot_vfat_summary(VFAT, STRIP, fit_filename):
    from ROOT import TFile,TCanvas,gStyle,TH2D

    fitF = TFile(fit_filename)
    if options.channels:
        vNoise = TH2D('vNoise', 'Noise vs trim for VFAT %i Channel %i; trimDAC [DAC units]; Noise [DAC units]'%(VFAT, STRIP), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    else:
        vNoise = TH2D('vNoise', 'Noise vs trim for VFAT %i Strip %i; trimDAC [DAC units]; Noise [DAC units]'%(VFAT, STRIP), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    vNoise.GetYaxis().SetTitleOffset(1.5)
    for event in fitF.scurveFitTree:
        if (event.vfatN == VFAT) and ((event.vfatstrip == STRIP and not options.channels) or (event.vfatCH == STRIP and options.channels)):
            vNoise.Fill(event.trimDAC, event.noise)
            pass
        pass
    canvas = TCanvas('canvas', 'canvas', 500, 500)
    gStyle.SetOptStat(0)
    vNoise.Draw('colz')
    canvas.Update()
    if options.channels:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Channel_%i.png'%(VFAT, STRIP))
        pass
    else:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Strip_%i.png'%(VFAT, STRIP))
        pass
    return

plot_vfat_summary(options.vfat, options.strip, options.filename)
