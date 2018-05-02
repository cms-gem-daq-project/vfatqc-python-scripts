#
# Makefile for vfatqc package
#

BUILD_HOME := $(shell dirname `pwd`)

Project      := vfatqc-python-scripts
ShortProject := vfatqc
Namespace    := gempython
Package      := vfatqc-python-scripts
ShortPackage := vfatqc
LongPackage  := vfatqc
PackageName  := $(Namespace)_$(ShortPackage)
PackageDir   := pkg/$(Namespace)/$(ShortPackage)
ScriptDir    := pkg/$(Namespace)/scripts


# Explicitly define the modules that are being exported (for PEP420 compliance)
PythonModules = ["$(Namespace).$(ShortPackage)"]
$(info PythonModules=${PythonModules})

VFATQC_VER_MAJOR=1
VFATQC_VER_MINOR=0
VFATQC_VER_PATCH=4

include $(BUILD_HOME)/$(Project)/config/mfCommonDefs.mk
include $(BUILD_HOME)/$(Project)/config/mfPythonDefs.mk

# include $(BUILD_HOME)/$(Project)/config/mfDefs.mk

include $(BUILD_HOME)/$(Project)/config/mfPythonRPM.mk

default:
	@echo "Running default target"
	$(MakeDir) $(PackageDir)
	@cp -rfp qcoptions.py $(PackageDir)
	@cp -rfp qcutilities.py $(PackageDir)
	@echo "__path__ = __import__('pkgutil').extend_path(__path__, __name__)" > pkg/$(Namespace)/__init__.py
	@cp -rfp __init__.py $(PackageDir)

# need to ensure that the python only stuff is packaged into RPMs
.PHONY: clean preprpm
_rpmprep: preprpm
	@echo "Running _rpmprep target"
preprpm: default
	@echo "Running preprpm target"
	@cp -rfp config/scriptlets/installrpm.sh pkg/
	$(MakeDir) $(ScriptDir)
	@cp -rfp run_scans.py   $(ScriptDir)
	@cp -rfp trimChamber.py $(ScriptDir)
	@cp -rfp fastLatency.py $(ScriptDir)
	@cp -rfp ultra*.py      $(ScriptDir)
	@cp -rfp conf*.py       $(ScriptDir)
	-cp -rfp README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt $(PackageDir)
	-cp -rfp README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt pkg

clean:
	@echo "Running clean target"
	-rm -rf $(ScriptDir)
	-rm -rf $(PackageDir)
	-rm -f  pkg/$(Namespace)/__init__.py
	-rm -f  pkg/README.md
	-rm -f  pkg/LICENSE
	-rm -f  pkg/MANIFEST.in
	-rm -f  pkg/CHANGELOG.md
	-rm -f  pkg/requirements.txt
	-rm -f  pkg/installrpm.sh

print-env:
	@echo BUILD_HOME     $(BUILD_HOME)
	@echo GIT_VERSION    $(GIT_VERSION)
	@echo PYTHON_VERSION $(PYTHON_VERSION)
	@echo GEMDEVELOPER   $(GEMDEVELOPER)
