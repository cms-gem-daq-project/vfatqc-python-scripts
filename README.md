# vfatqc-python-scriptsi

1. For VFAT2s QC test:
   
	> python pythonScript.py

	>> GLIB IP: e.g. 192.168.0.171

	>> QC Test Name: e.g. 2016_09_09_QC3

	Then hit "enter" 5 times 

2. To plot each VFAT's output results: (all the output files should in the same dir)
   
	> python read_and_plot.py

3. To plot all VFATs' results: (all the output files should in the same dir)
   
	> python read_and_plot_all.py

4. To set the TrimDAC values: 
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt
   
	> python setTRIMDAC.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 

5. To set the TrimDAC values and make the S-Curve scanning:
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt
   
	> python setTRIMDAC_and_Scurve.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 

6. To set the TrimDAC values, set thresholds and make the S-Curve scanning:
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt

	Second, make a txt file to list all the Threshold files: Datafiles.txt
   
	> python setTRIMDAC_and_Threshold.py

	>> GLIB IP:  e.g. 192.168.0.171

	>> Test Name: e.g. 2016_09_09_SetTrimDAC

	Then hit "enter" 5 times 





