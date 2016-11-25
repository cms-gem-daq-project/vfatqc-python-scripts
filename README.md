# vfatqc-python-scriptsi

1. For VFAT2s QC1 test:
   
	> python testing.py

	>> GLIB IP: e.g. 192.168.0.171

	Then hit "enter" 5 times 

2. For VFAT2s QC2/3 test: (Off detector: 35~40 mins per chip; On detector: 55~60 mins per chip!)
   
	> python pythonScript.py

	>> GLIB IP: e.g. 192.168.0.171

	>> QC Test Name: <yy>_<mm>_<dd>_<testName> e.g. 2016_09_09_QC3

	Then hit "enter" 5 times 

3. To save VFAT's output results as root files: (all the output files should in the same dir)
   
	> // Each VFAT has a rootfile: <yy>_<mm>_<dd>_<testName>_<xxxxxx>
	> // e.g. 2016_11_10_OnDetNoVoltageSCurveBot_VFAT0_ID_0xf6e7_ScurveOutput.root
	> // All VFATs from one detector will have a combined rootfile: ScurveOutput.root
	> #python ProduceRootFiles.py
	
	To plot each VFAT's output results: (all the output files should in the same dir)
   
	> python read_and_plot.py
	
	To plot all VFATs' results: (all the output files should in the same dir)
   
	> python read_and_plot_all.py

4. To mask the channels and plot 1 s-curve for each VFAT in different ieat region 
   
	> // The only input file: ScurveOutput.root
	> // L41-77: plotting s-curve for different ieat region, e.g. iEta_1_ScurveAF.pdf
	> // For the failed VFAT, modify L68 or L61 or L54.
	> // In case you only need to mask the channels, please comment L41-77.
	> // Channles masking: e.g. Mask_TRIM_DAC_value_VFAT0_ID_0xf6e7
	> // Colllection of all bad channels: All_Bad_Channels_to_Mask
	> #python MaskChannels.py

5. To set the TrimDAC values and scan the threshold: (70~80s 24 chips!) 
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt
   
	> python setTRIMDAC.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 

6. To set the TrimDAC values and make the S-Curve scanning: (8~15 mins per chip!)
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt
   
	> python setTRIMDAC_and_Scurve.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 

7. (Not a good idea!!) To set the TrimDAC values, set thresholds and make the S-Curve scanning:
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt

	Second, make a txt file to list all the Threshold files: Datafiles.txt
   
	> python setTRIMDAC_and_Threshold.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 





