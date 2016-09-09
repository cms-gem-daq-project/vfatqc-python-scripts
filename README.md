# vfatqc-python-scriptsi

1. For VFAT2s QC test:
   
	pythong pythonScript.py

	>>> GLIB IP: <your ip>, e.g. 192.168.0.171

	>>> QC Test Name: <your test name>, e.g. 2016_09_09_QC3

2. To plot each VFAT's output results: (all the output files should in the same dir)
   
	python read_and_plot.py

3. To make all VFATs' results: (all the output files should in the same dir)
   
	python read_and_plot_all.py

4. To set the TrimDAC values: 
   
	First, we need to make a txt file to list all the TrimDAC files: TrimDACfiles.txt
   
	python setTRIMDAC.py

	>>> GLIB IP: <your ip>

	>>> Test Name: <your test name>


